import { startTransition, useEffect, useState } from 'react'

type IntakeResult = {
  intake_session_id: string
  language: string
  patient_age_group: string
  primary_symptom: string
  symptom_category: string
  duration_hours: number
  severity_indicators: string[]
  emergency_flags: string[]
  emergency_stop: boolean
  provisional_ctas_level: number
  provisional_ctas_label: string
  recommended_facility_type: string
  recommended_urgency_band: string
  queue_eligible: boolean
  reasoning_summary: string
}

type Recommendation = {
  facility_id_normalized: string
  facility_name: string
  odhf_facility_type?: string
  city?: string
  wait_time_non_priority_minutes?: number
  people_waiting?: number
  stretcher_occupancy_pct?: number
  virtual_queue_depth?: number
  avg_wait_room_minutes_prev_day?: number
  avg_stretcher_wait_minutes_prev_day?: number
  estimated_total_time_minutes?: number
  distance_km?: number
  fit_for_ctas?: string
  score: number
}

type Reservation = {
  queue_id: string
  queue_position: number
  estimated_call_time: string
  queue_status: string
}

type QueueTracking = Reservation & {
  facility_name: string
  city: string
  remaining_minutes: number
  leave_now_recommendation: boolean
}

type StaffRow = {
  facility_id: string
  facility_name: string
  city: string
  odhf_facility_type: string
  incoming_queue_count: number
  arrivals_next_2h: number
  avg_live_wait_minutes: number
  avg_stretcher_occupancy_pct: number
  ctas_1_count: number
  ctas_2_count: number
  ctas_3_count: number
  ctas_4_count: number
  ctas_5_count: number
}

const copy = {
  en: {
    title: 'SalleQ',
    subtitle: 'Quebec-first virtual non-emergency waiting room with AI-assisted routing support',
    disclaimer:
      'Do not use this service for emergencies. AI-estimated provisional CTAS urgency for routing support only. Final triage is determined by clinical staff.',
    consent: 'I understand this service is for non-emergency use only.',
    continue: 'Continue',
    locate: 'Use my location',
    analyze: 'Analyze symptoms',
    recommendations: 'Recommended facilities',
    reserve: 'Reserve queue slot',
    tracking: 'Queue tracking',
    staff: 'Staff operations',
    patient: 'Patient flow',
  },
  fr: {
    title: 'SalleQ',
    subtitle: "Salle d'attente virtuelle québécoise pour les cas non urgents avec soutien IA",
    disclaimer:
      "N'utilisez pas ce service en cas d'urgence. Urgence CTAS provisoire estimée par IA à titre de soutien au routage seulement. Le triage final est déterminé par le personnel clinique.",
    consent: "Je comprends que ce service est réservé aux situations non urgentes.",
    continue: 'Continuer',
    locate: 'Utiliser ma position',
    analyze: 'Analyser les symptômes',
    recommendations: 'Établissements recommandés',
    reserve: 'Réserver une place',
    tracking: 'Suivi de file',
    staff: 'Opérations du personnel',
    patient: 'Parcours patient',
  },
} as const

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })
  const payload = await response.json()
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.detail ?? payload.error ?? 'Request failed')
  }
  return payload.data as T
}

function MetricCard(props: { label: string; value: string | number; tone?: 'default' | 'alert' | 'ok' }) {
  return (
    <div className={`metric-card metric-card--${props.tone ?? 'default'}`}>
      <div className="metric-label">{props.label}</div>
      <div className="metric-value">{props.value}</div>
    </div>
  )
}

function App() {
  const [mode, setMode] = useState<'patient' | 'staff'>('patient')
  const [language, setLanguage] = useState<'en' | 'fr'>('en')
  const [patientStep, setPatientStep] = useState<1 | 2 | 3 | 4 | 5 | 99>(1)
  const [consentAccepted, setConsentAccepted] = useState(false)
  const [location, setLocation] = useState<{ latitude: number; longitude: number } | null>(null)
  const [symptomText, setSymptomText] = useState('')
  const [ageGroup, setAgeGroup] = useState('adult')
  const [intake, setIntake] = useState<IntakeResult | null>(null)
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [selectedFacility, setSelectedFacility] = useState<Recommendation | null>(null)
  const [notificationPreference, setNotificationPreference] = useState('none')
  const [contactValue, setContactValue] = useState('')
  const [arrivalWindowStart, setArrivalWindowStart] = useState('')
  const [arrivalWindowEnd, setArrivalWindowEnd] = useState('')
  const [reservation, setReservation] = useState<Reservation | null>(null)
  const [tracking, setTracking] = useState<QueueTracking | null>(null)
  const [staffSummary, setStaffSummary] = useState<StaffRow[]>([])
  const [staffDetail, setStaffDetail] = useState<Record<string, unknown>[]>([])
  const [selectedStaffFacility, setSelectedStaffFacility] = useState<string>('')
  const [staffQuestion, setStaffQuestion] = useState('What is the next 2-hour arrival load for my site?')
  const [staffAnswer, setStaffAnswer] = useState('')
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const t = copy[language]

  useEffect(() => {
    if (mode !== 'staff') {
      return
    }
    startTransition(() => {
      void loadStaffSummary()
    })
  }, [mode])

  useEffect(() => {
    if (!reservation || patientStep !== 5) {
      return
    }
    void loadQueueTracking(reservation.queue_id)
    const interval = window.setInterval(() => void loadQueueTracking(reservation.queue_id), 30000)
    return () => window.clearInterval(interval)
  }, [reservation, patientStep, location])

  async function requestGeolocation() {
    if (!navigator.geolocation) {
      setError('Geolocation is not available in this browser.')
      return
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        })
      },
      () => setError('Location permission was denied. You can continue without it.'),
    )
  }

  async function submitIntake() {
    if (!symptomText.trim()) {
      setError('Please describe the symptoms before continuing.')
      return
    }
    setError(null)
    setLoading('Analyzing symptoms')
    try {
      const payload = await apiFetch<IntakeResult>('/api/patient/intake', {
        method: 'POST',
        body: JSON.stringify({
          symptom_text: symptomText,
          patient_age_group: ageGroup,
          language,
        }),
      })
      setIntake(payload)
      if (payload.emergency_stop) {
        setPatientStep(99)
        return
      }
      const nextRecommendations = await loadRecommendations(payload.intake_session_id)
      if (nextRecommendations.length > 0) {
        setSelectedFacility(nextRecommendations[0])
        initializeReservationWindow()
      }
      setPatientStep(3)
    } catch (caught) {
      setError((caught as Error).message)
    } finally {
      setLoading(null)
    }
  }

  async function loadRecommendations(intakeSessionId: string) {
    const query = location
      ? `?latitude=${location.latitude}&longitude=${location.longitude}`
      : ''
    const payload = await apiFetch<Recommendation[]>(`/api/patient/recommendations/${intakeSessionId}${query}`)
    setRecommendations(payload)
    return payload
  }

  function initializeReservationWindow() {
    const start = new Date()
    start.setMinutes(Math.ceil(start.getMinutes() / 15) * 15)
    const end = new Date(start.getTime() + 45 * 60000)
    setArrivalWindowStart(start.toISOString().slice(0, 16))
    setArrivalWindowEnd(end.toISOString().slice(0, 16))
  }

  async function reserveSelectedFacility() {
    if (!intake || !selectedFacility) {
      setError('Select a facility first.')
      return
    }
    setLoading('Reserving queue slot')
    setError(null)
    try {
      const payload = await apiFetch<Reservation>('/api/patient/reserve', {
        method: 'POST',
        body: JSON.stringify({
          intake_session_id: intake.intake_session_id,
          facility_id: selectedFacility.facility_id_normalized,
          arrival_window_start: new Date(arrivalWindowStart).toISOString(),
          arrival_window_end: new Date(arrivalWindowEnd).toISOString(),
          notification_preference: notificationPreference,
          channel_type: notificationPreference,
          contact_value: contactValue || null,
        }),
      })
      setReservation(payload)
      setPatientStep(5)
    } catch (caught) {
      setError((caught as Error).message)
    } finally {
      setLoading(null)
    }
  }

  async function loadQueueTracking(queueId: string) {
    const query = location
      ? `?latitude=${location.latitude}&longitude=${location.longitude}`
      : ''
    try {
      const payload = await apiFetch<QueueTracking>(`/api/patient/track/${queueId}${query}`)
      setTracking(payload)
    } catch (caught) {
      setError((caught as Error).message)
    }
  }

  async function loadStaffSummary() {
    try {
      setLoading('Loading staff dashboard')
      const payload = await apiFetch<{ user: string; rows: StaffRow[] }>('/api/staff/summary')
      setStaffSummary(payload.rows)
      if (payload.rows[0]) {
        setSelectedStaffFacility(payload.rows[0].facility_id)
        await loadStaffFacility(payload.rows[0].facility_id)
      }
      setError(null)
    } catch (caught) {
      setError((caught as Error).message)
    } finally {
      setLoading(null)
    }
  }

  async function loadStaffFacility(facilityId: string) {
    try {
      const payload = await apiFetch<Record<string, unknown>[]>(`/api/staff/facility/${facilityId}`)
      setStaffDetail(payload)
      setSelectedStaffFacility(facilityId)
    } catch (caught) {
      setError((caught as Error).message)
    }
  }

  async function askStaffAssistant() {
    try {
      setLoading('Asking staff assistant')
      const payload = await apiFetch<{ answer: string }>('/api/staff/assistant', {
        method: 'POST',
        body: JSON.stringify({ question: staffQuestion }),
      })
      setStaffAnswer(payload.answer)
      setError(null)
    } catch (caught) {
      setError((caught as Error).message)
    } finally {
      setLoading(null)
    }
  }

  const totalStaffQueue = staffSummary.reduce((sum, row) => sum + Number(row.incoming_queue_count || 0), 0)
  const totalNextTwoHours = staffSummary.reduce((sum, row) => sum + Number(row.arrivals_next_2h || 0), 0)
  const highestCongestion = [...staffSummary].sort(
    (left, right) => Number(right.avg_stretcher_occupancy_pct || 0) - Number(left.avg_stretcher_occupancy_pct || 0),
  )[0]

  return (
    <div className="shell">
      <header className="hero-panel">
        <div>
          <div className="eyebrow">Databricks App · Quebec hackathon build</div>
          <h1>{t.title}</h1>
          <p className="hero-copy">{t.subtitle}</p>
          <p className="disclaimer-banner">{t.disclaimer}</p>
        </div>
        <div className="hero-actions">
          <div className="language-toggle">
            <button className={language === 'en' ? 'is-active' : ''} onClick={() => setLanguage('en')}>
              EN
            </button>
            <button className={language === 'fr' ? 'is-active' : ''} onClick={() => setLanguage('fr')}>
              FR
            </button>
          </div>
          <div className="mode-toggle">
            <button className={mode === 'patient' ? 'is-active' : ''} onClick={() => setMode('patient')}>
              {t.patient}
            </button>
            <button className={mode === 'staff' ? 'is-active' : ''} onClick={() => setMode('staff')}>
              {t.staff}
            </button>
          </div>
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}
      {loading ? <div className="loading-banner">{loading}...</div> : null}

      {mode === 'patient' ? (
        <main className="content-grid">
          <section className="primary-panel">
            <div className="stepper">
              {['Consent', 'Intake', 'Facilities', 'Reservation', 'Tracking'].map((step, index) => (
                <div key={step} className={`step ${patientStep === index + 1 ? 'is-active' : patientStep > index + 1 ? 'is-complete' : ''}`}>
                  <span>{index + 1}</span>
                  <label>{step}</label>
                </div>
              ))}
            </div>

            {patientStep === 1 ? (
              <section className="screen-card">
                <h2>Landing and consent</h2>
                <p>
                  {language === 'fr'
                    ? "SalleQ oriente les patients non urgents vers le bon établissement. En cas d'urgence, appelez les services d'urgence ou rendez-vous immédiatement à l'urgence."
                    : 'SalleQ helps route non-emergency patients to the right facility. For emergencies, call emergency services or go directly to the ER.'}
                </p>
                <label className="checkbox-row">
                  <input type="checkbox" checked={consentAccepted} onChange={(event) => setConsentAccepted(event.target.checked)} />
                  <span>{t.consent}</span>
                </label>
                <div className="button-row">
                  <button className="secondary-button" onClick={requestGeolocation}>
                    {t.locate}
                  </button>
                  <button className="primary-button" disabled={!consentAccepted} onClick={() => setPatientStep(2)}>
                    {t.continue}
                  </button>
                </div>
                {location ? <div className="info-chip">Location captured for distance-aware facility ranking.</div> : null}
              </section>
            ) : null}

            {patientStep === 2 ? (
              <section className="screen-card">
                <h2>Symptom intake</h2>
                <div className="form-grid">
                  <label>
                    Age group
                    <select value={ageGroup} onChange={(event) => setAgeGroup(event.target.value)}>
                      <option value="infant">Infant</option>
                      <option value="child">Child</option>
                      <option value="adult">Adult</option>
                      <option value="older_adult">Older adult</option>
                    </select>
                  </label>
                  <label className="full-width">
                    Describe symptoms
                    <textarea
                      rows={7}
                      value={symptomText}
                      onChange={(event) => setSymptomText(event.target.value)}
                      placeholder={
                        language === 'fr'
                          ? "Ex. fièvre depuis 12 heures, douleur à la gorge, peut boire mais douleur modérée."
                          : 'E.g. fever for 12 hours, sore throat, able to drink fluids, moderate pain.'
                      }
                    />
                  </label>
                </div>
                <div className="button-row">
                  <button className="secondary-button" onClick={() => setPatientStep(1)}>
                    Back
                  </button>
                  <button className="primary-button" onClick={() => void submitIntake()}>
                    {t.analyze}
                  </button>
                </div>
              </section>
            ) : null}

            {patientStep === 99 && intake ? (
              <section className="screen-card emergency-panel">
                <h2>Emergency escalation</h2>
                <p>
                  Emergency indicators were detected. This queue flow is blocked and the patient should be routed to immediate emergency care.
                </p>
                <div className="badge-row">
                  {intake.emergency_flags.map((flag) => (
                    <span key={flag} className="flag-badge">
                      {flag}
                    </span>
                  ))}
                </div>
                <p className="emphasis">
                  {language === 'fr'
                    ? "Si la situation est urgente, composez le 911 ou rendez-vous immédiatement à l'urgence la plus proche."
                    : 'If this is urgent, call 911 or go to the nearest emergency department immediately.'}
                </p>
                <button className="secondary-button" onClick={() => setPatientStep(2)}>
                  Re-enter symptoms
                </button>
              </section>
            ) : null}

            {patientStep === 3 && intake ? (
              <section className="screen-card">
                <h2>{t.recommendations}</h2>
                <div className="summary-grid">
                  <MetricCard label="Primary symptom" value={intake.primary_symptom} />
                  <MetricCard label="Symptom category" value={intake.symptom_category} />
                  <MetricCard label="Provisional CTAS" value={`CTAS ${intake.provisional_ctas_level} · ${intake.provisional_ctas_label}`} tone={intake.provisional_ctas_level <= 3 ? 'alert' : 'ok'} />
                  <MetricCard label="Recommended facility type" value={intake.recommended_facility_type} />
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Facility</th>
                        <th>Type</th>
                        <th>City</th>
                        <th>Distance</th>
                        <th>Wait</th>
                        <th>People waiting</th>
                        <th>Stretcher occupancy</th>
                        <th>Estimated total</th>
                        <th>Fit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recommendations.map((facility) => (
                        <tr
                          key={facility.facility_id_normalized}
                          className={selectedFacility?.facility_id_normalized === facility.facility_id_normalized ? 'is-selected' : ''}
                          onClick={() => setSelectedFacility(facility)}
                        >
                          <td>{facility.facility_name}</td>
                          <td>{facility.odhf_facility_type || 'Unknown'}</td>
                          <td>{facility.city || '—'}</td>
                          <td>{facility.distance_km ? `${facility.distance_km.toFixed(1)} km` : '—'}</td>
                          <td>{facility.wait_time_non_priority_minutes ?? '—'} min</td>
                          <td>{facility.people_waiting ?? '—'}</td>
                          <td>{facility.stretcher_occupancy_pct ?? '—'}%</td>
                          <td>{facility.estimated_total_time_minutes ?? '—'} min</td>
                          <td>{facility.fit_for_ctas}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="button-row">
                  <button className="secondary-button" onClick={() => setPatientStep(2)}>
                    Back
                  </button>
                  <button className="primary-button" disabled={!selectedFacility || !intake.queue_eligible} onClick={() => setPatientStep(4)}>
                    {t.reserve}
                  </button>
                </div>
                {!intake.queue_eligible ? (
                  <div className="info-chip">Virtual queue enrollment is disabled for this CTAS routing band.</div>
                ) : null}
              </section>
            ) : null}

            {patientStep === 4 && selectedFacility ? (
              <section className="screen-card">
                <h2>Queue reservation</h2>
                <div className="facility-summary">
                  <div>
                    <strong>{selectedFacility.facility_name}</strong>
                    <div>{selectedFacility.city}</div>
                    <div>{selectedFacility.odhf_facility_type}</div>
                  </div>
                  <div className="mini-kpis">
                    <span>{selectedFacility.wait_time_non_priority_minutes ?? '—'} min wait</span>
                    <span>{selectedFacility.people_waiting ?? '—'} waiting</span>
                    <span>{selectedFacility.stretcher_occupancy_pct ?? '—'}% occupancy</span>
                  </div>
                </div>
                <div className="form-grid">
                  <label>
                    Arrival window start
                    <input type="datetime-local" value={arrivalWindowStart} onChange={(event) => setArrivalWindowStart(event.target.value)} />
                  </label>
                  <label>
                    Arrival window end
                    <input type="datetime-local" value={arrivalWindowEnd} onChange={(event) => setArrivalWindowEnd(event.target.value)} />
                  </label>
                  <label>
                    Notification preference
                    <select value={notificationPreference} onChange={(event) => setNotificationPreference(event.target.value)}>
                      <option value="none">No notifications</option>
                      <option value="sms">SMS</option>
                      <option value="email">Email</option>
                    </select>
                  </label>
                  <label>
                    Contact value
                    <input
                      value={contactValue}
                      onChange={(event) => setContactValue(event.target.value)}
                      placeholder="Only needed for SMS or email notifications"
                    />
                  </label>
                </div>
                <div className="button-row">
                  <button className="secondary-button" onClick={() => setPatientStep(3)}>
                    Back
                  </button>
                  <button className="primary-button" onClick={() => void reserveSelectedFacility()}>
                    Confirm reservation
                  </button>
                </div>
              </section>
            ) : null}

            {patientStep === 5 && reservation && tracking ? (
              <section className="screen-card">
                <h2>{t.tracking}</h2>
                <div className="summary-grid">
                  <MetricCard label="Queue number" value={tracking.queue_id} />
                  <MetricCard label="Position" value={tracking.queue_position} />
                  <MetricCard label="Remaining" value={`${tracking.remaining_minutes} min`} />
                  <MetricCard label="Status" value={tracking.queue_status} tone={tracking.leave_now_recommendation ? 'ok' : 'default'} />
                </div>
                <div className="tracking-card">
                  <p>
                    <strong>{tracking.facility_name}</strong> · {tracking.city}
                  </p>
                  <p>Estimated call time: {new Date(tracking.estimated_call_time).toLocaleString()}</p>
                  <p>
                    {tracking.leave_now_recommendation
                      ? 'Travel now to align with the estimated call time.'
                      : 'You can continue waiting remotely for now.'}
                  </p>
                </div>
              </section>
            ) : null}
          </section>

          <aside className="side-panel">
            <div className="screen-card compact-card">
              <h3>Clinical safety notice</h3>
              <p>
                AI-estimated provisional CTAS urgency for routing support only. Final triage is determined by clinical staff.
              </p>
            </div>
            {intake ? (
              <div className="screen-card compact-card">
                <h3>Intake summary</h3>
                <ul className="summary-list">
                  <li>Primary symptom: {intake.primary_symptom}</li>
                  <li>Category: {intake.symptom_category}</li>
                  <li>Urgency: CTAS {intake.provisional_ctas_level}</li>
                  <li>Emergency flags: {intake.emergency_flags.length ? intake.emergency_flags.join(', ') : 'None'}</li>
                </ul>
              </div>
            ) : null}
          </aside>
        </main>
      ) : (
        <main className="staff-layout">
          <section className="staff-main">
            <div className="screen-card">
              <div className="section-heading">
                <div>
                  <h2>Staff dashboard home</h2>
                  <p>Scoped operational view backed by Unity Catalog-secured staff views.</p>
                </div>
                <button className="secondary-button" onClick={() => void loadStaffSummary()}>
                  Refresh
                </button>
              </div>
              <div className="summary-grid">
                <MetricCard label="Incoming queue count" value={totalStaffQueue} />
                <MetricCard label="Arrivals next 2 hours" value={totalNextTwoHours} />
                <MetricCard label="Facilities in scope" value={staffSummary.length} />
                <MetricCard
                  label="Highest congestion facility"
                  value={highestCongestion ? highestCongestion.facility_name : 'No scoped data'}
                  tone={highestCongestion ? 'alert' : 'default'}
                />
              </div>
            </div>

            <div className="screen-card">
              <h3>Facility operations</h3>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Facility</th>
                      <th>Arrivals next 2h</th>
                      <th>Incoming queue</th>
                      <th>Average live wait</th>
                      <th>CTAS 4-5</th>
                    </tr>
                  </thead>
                  <tbody>
                    {staffSummary.map((row) => (
                      <tr
                        key={row.facility_id}
                        className={selectedStaffFacility === row.facility_id ? 'is-selected' : ''}
                        onClick={() => void loadStaffFacility(row.facility_id)}
                      >
                        <td>
                          <strong>{row.facility_name}</strong>
                          <div className="table-subtitle">{row.city}</div>
                        </td>
                        <td>{row.arrivals_next_2h}</td>
                        <td>{row.incoming_queue_count}</td>
                        <td>{Math.round(row.avg_live_wait_minutes || 0)} min</td>
                        <td>{(row.ctas_4_count || 0) + (row.ctas_5_count || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="screen-card">
              <h3>Facility detail view</h3>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Queue ID</th>
                      <th>Primary symptom</th>
                      <th>CTAS</th>
                      <th>Arrival window</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {staffDetail.map((row) => (
                      <tr key={String(row.queue_id)}>
                        <td>{String(row.queue_id)}</td>
                        <td>{String(row.primary_symptom ?? '—')}</td>
                        <td>{String(row.provisional_ctas_label ?? '—')}</td>
                        <td>{String(row.arrival_window_start ?? '—')}</td>
                        <td>{String(row.queue_status ?? '—')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <aside className="assistant-panel">
            <div className="screen-card">
              <h3>Embedded Staff AI Assistant</h3>
              <p>This assistant complements the dashboard. It does not replace the staff UI.</p>
              <textarea rows={6} value={staffQuestion} onChange={(event) => setStaffQuestion(event.target.value)} />
              <button className="primary-button full-width" onClick={() => void askStaffAssistant()}>
                Ask operations agent
              </button>
              <div className="assistant-answer">{staffAnswer || 'Ask about next 2-hour load, CTAS mix, or congestion.'}</div>
            </div>
          </aside>
        </main>
      )}
    </div>
  )
}

export default App
