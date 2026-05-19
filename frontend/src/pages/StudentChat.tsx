import React, { useEffect, useRef, useState } from 'react'
import { api } from '../api/studyowl'
import type { StudentProgress } from '../api/studyowl'
import HintBubble from '../components/HintBubble'
import { useAuth } from '../auth/AuthContext'
import PhotoUpload from '../components/PhotoUpload'
import ProgressChart from '../components/ProgressChart'
import QuestionHistoryPanel from '../components/QuestionHistoryPanel'

interface LearningResource {
  title: string
  url?: string
  summary?: string
}

export const StudentChat: React.FC = () => {
  const { user } = useAuth()
  const [question, setQuestion] = useState('')
  const [photoB64, setPhotoB64] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [hint, setHint] = useState<string | null>(null)
  const [hintLevel, setHintLevel] = useState<1 | 2 | 3>(1)
  const [attempt, setAttempt] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'answered'>('idle')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reviewMode, setReviewMode] = useState(false)
  const [learningResources, setLearningResources] = useState<LearningResource[]>([])
  const [sessionStage, setSessionStage] = useState<'start' | 'inProgress' | 'complete'>('start')
  const [finalAnswer, setFinalAnswer] = useState<string | null>(null)
  const [progress, setProgress] = useState<StudentProgress | null>(null)
  const [progressError, setProgressError] = useState<string | null>(null)
  const analyticsDialogRef = useRef<HTMLDialogElement>(null)

  const openAnalyticsDetails = () => analyticsDialogRef.current?.showModal()
  const closeAnalyticsDetails = () => analyticsDialogRef.current?.close()
  const handleAnalyticsBackdrop = (e: React.MouseEvent<HTMLDialogElement>) => {
    if (e.target === analyticsDialogRef.current) closeAnalyticsDetails()
  }

  const handleStartSession = async () => {
    if (!question.trim() && !photoB64) {
      setError('Please enter a homework question or attach a photo')
      return
    }

    setStatus('loading')
    setError(null)
    setReviewMode(false)
    setLearningResources([])

    try {
      const result = await api.startSession({
        question,
        photo_b64: photoB64 ?? undefined,
      })
      setSessionId(result.session_id)
      setSessionStage('inProgress')
      setHint(result.hint)
      setHintLevel(result.hint_level)
      setAttempt('')
      setPhotoB64(null)
      setStatus('idle')
      setMessage(null)
    } catch (err) {
      setError((err as Error).message)
      setStatus('idle')
    }
  }

  const handleSubmitAttempt = async () => {
    if (!sessionId || !attempt.trim()) return

    setStatus('loading')
    setError(null)

    try {
      const result = await api.submitAttempt(sessionId, { attempt_text: attempt })

      if (result.status === 'correct') {
        setMessage('You got it! Great work!')
        setReviewMode(false)
        setLearningResources([])
        setFinalAnswer(null)
        setSessionStage('complete')
        setAttempt('')
      } else {
        setHint(result.hint ?? null)
        setHintLevel(result.hint_level ?? hintLevel)
        setMessage(result.message ?? null)
        setReviewMode(result.review_mode ?? false)
        setLearningResources(result.learning_resources ?? [])
        setFinalAnswer(result.final_answer ?? null)
        setAttempt('')
      }
      setStatus('idle')
    } catch (err) {
      setError((err as Error).message)
      setStatus('idle')
    }
  }

  const handleNextProblem = () => {
    setSessionId(null)
    setSessionStage('start')
    setQuestion('')
    setPhotoB64(null)
    setHint(null)
    setHintLevel(1)
    setAttempt('')
    setMessage(null)
    setError(null)
    setReviewMode(false)
    setFinalAnswer(null)
    setLearningResources([])
  }

  const handleHistorySelect = (text: string) => {
    if (sessionStage !== 'start') handleNextProblem()
    setQuestion(text)
    setPhotoB64(null)
    setError(null)
    document
      .getElementById('question-textarea')
      ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  useEffect(() => {
    // ProtectedRoute guarantees user is non-null here, but guard anyway.
    if (!user) {
      setProgressError('Unable to load your progress.')
      return
    }

    api.getProgress(user.id)
      .then((data) => setProgress(data))
      .catch((err) => setProgressError(err.message))
  }, [user])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-3 sm:p-4">
      <div className="max-w-2xl mx-auto">
        <header className="text-center mb-6 sm:mb-8 pt-4 sm:pt-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-indigo-900 mb-2">
            🦉 StudyOwl
          </h1>
          <p className="text-gray-600">Your AI Homework Assistant</p>
        </header>

        <div className="grid gap-4 sm:gap-6 mb-6 lg:grid-cols-3 items-start">
          <div className="lg:col-span-2 rounded-3xl bg-white/90 shadow-lg border border-indigo-100 overflow-hidden">
            <div className="flex items-center justify-between gap-3 px-4 sm:px-6 pt-4 sm:pt-6 pb-3">
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-xl" aria-hidden="true">📊</span>
                <h2 className="text-xl font-semibold text-indigo-900 truncate">Homework Analytics</h2>
              </div>
              {progress && progress.subjects.length > 0 && (
                <button
                  type="button"
                  onClick={openAnalyticsDetails}
                  className="inline-flex items-center gap-1 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs sm:text-sm font-semibold text-indigo-700 hover:bg-indigo-100 transition whitespace-nowrap"
                >
                  View details
                  <span aria-hidden="true">→</span>
                </button>
              )}
            </div>

            <div className="px-4 sm:px-6 pb-4 sm:pb-6">
              {progressError ? (
                <p className="text-sm text-red-600">{progressError}</p>
              ) : progress ? (
                <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                  <div className="rounded-2xl bg-indigo-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-indigo-600">Subjects Tracked</p>
                    <p className="mt-2 text-3xl font-bold text-indigo-900">{progress.subjects.length}</p>
                  </div>
                  <div className="rounded-2xl bg-sky-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-sky-600">Success Rate</p>
                    <p className="mt-2 text-3xl font-bold text-sky-900">{Math.round(progress.subjects.reduce((sum, item) => sum + item.success_rate, 0) / (progress.subjects.length || 1) * 100) / 100}%</p>
                  </div>
                  <div className="rounded-2xl bg-emerald-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-emerald-600">Recent Sessions</p>
                    <p className="mt-2 text-3xl font-bold text-emerald-900">{progress.recent_sessions.length}</p>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-500">Loading your learning progress...</p>
              )}
            </div>
          </div>

          <div className="rounded-3xl bg-white/90 p-4 sm:p-6 shadow-lg border border-indigo-100">
            <h2 className="text-xl font-semibold text-indigo-900 mb-3">Quick Tip</h2>
            <p className="text-sm text-slate-600">
              Track your progress on each subject, then use the hints below to build confidence before the final step.
            </p>
          </div>
        </div>

        <dialog
          ref={analyticsDialogRef}
          onClick={handleAnalyticsBackdrop}
          aria-labelledby="analytics-dialog-title"
          className="m-auto rounded-3xl bg-white shadow-2xl p-0 backdrop:bg-slate-900/50 w-[min(640px,calc(100vw-1.5rem))] max-h-[calc(100vh-2rem)]"
        >
          {progress && (
            <div className="flex flex-col max-h-[inherit]">
              <header className="flex items-center justify-between gap-3 border-b border-slate-100 px-5 sm:px-6 pt-5 sm:pt-6 pb-3">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-xl" aria-hidden="true">📊</span>
                  <h3 id="analytics-dialog-title" className="text-lg sm:text-xl font-semibold text-indigo-900 truncate">
                    Analytics — Details
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={closeAnalyticsDetails}
                  aria-label="Close details"
                  className="rounded-full p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition"
                >
                  <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path
                      fillRule="evenodd"
                      d="M4.293 4.293a1 1 0 0 1 1.414 0L10 8.586l4.293-4.293a1 1 0 1 1 1.414 1.414L11.414 10l4.293 4.293a1 1 0 0 1-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 0 1-1.414-1.414L8.586 10 4.293 5.707a1 1 0 0 1 0-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </header>

              <div className="overflow-y-auto px-5 sm:px-6 py-4 sm:py-5 space-y-4">
                {progress.subjects.length > 0 && (
                  <ProgressChart
                    data={progress.subjects.map((s) => ({
                      subject: s.name,
                      sessions: s.sessions,
                      success_rate: Math.round(s.success_rate * 100),
                    }))}
                  />
                )}
                <div className="space-y-3">
                  {progress.subjects.map((subject) => (
                    <div key={subject.name} className="rounded-2xl bg-slate-50 p-4 border border-slate-200">
                      <div className="flex items-center justify-between gap-4">
                        <p className="font-semibold text-slate-900">{subject.name}</p>
                        <p className="text-sm text-slate-500">{subject.sessions} sessions</p>
                      </div>
                      <div className="mt-3 h-2 rounded-full bg-white">
                        <div className="h-full rounded-full bg-indigo-500" style={{ width: `${subject.success_rate * 100}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </dialog>

        {user && (
          <div className="mb-6">
            <QuestionHistoryPanel studentId={user.id} onSelect={handleHistorySelect} />
          </div>
        )}

        <div className="bg-white rounded-lg shadow-lg p-4 sm:p-6 mb-6">
          {sessionStage === 'start' ? (
            <>
              <h2 className="text-2xl font-bold text-gray-800 mb-4">
                What are you working on?
              </h2>
              <textarea
                id="question-textarea"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Type or paste your homework question here..."
                className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-4"
              />
              <div className="mb-4">
                <PhotoUpload onPhotoCapture={setPhotoB64} loading={status === 'loading'} />
                {photoB64 && (
                  <div className="mt-3 flex items-center justify-between rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-2 text-sm">
                    <span className="text-indigo-900">📷 Photo attached — we'll read the problem from it.</span>
                    <button
                      type="button"
                      onClick={() => setPhotoB64(null)}
                      className="text-indigo-700 underline hover:text-indigo-900"
                    >
                      Remove
                    </button>
                  </div>
                )}
              </div>
              <button
                onClick={handleStartSession}
                disabled={status === 'loading'}
                className="w-full bg-indigo-600 text-white py-2 rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50 transition"
              >
                {status === 'loading' ? 'Loading...' : 'Get First Hint'}
              </button>
            </>
          ) : sessionStage === 'inProgress' ? (
            <>
             {message && (
                <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-4 rounded">
                  <p className="text-gray-800">{message}</p>
                </div>
              )}
              <div className="mb-6">
                <p className="text-gray-600 mb-2">Question:</p>
                <p className="text-gray-900 bg-gray-50 p-3 rounded-lg whitespace-pre-wrap break-words">
                  {question}
                </p>
              </div>

              {hint && <HintBubble hint={hint} level={hintLevel} />}

              {reviewMode && (
                <div className="relative overflow-hidden rounded-lg p-6 bg-gradient-to-br from-orange-50 via-white to-amber-50 border border-orange-200 mb-4">
                  <div className="celebration-wrapper pointer-events-none">
                    {Array.from({ length: 10 }).map((_, index) => (
                      <span
                        key={index}
                        className="confetti-piece"
                        style={{
                          left: `${8 + index * 8}%`,
                          animationDelay: `${index * 0.08}s`,
                          backgroundColor: ['#f59e0b', '#ea580c', '#d97706', '#f97316'][index % 4],
                        }}
                      />
                    ))}
                  </div>
                  <div className="relative">
                    <h2 className="text-3xl font-bold text-orange-900 mb-3 text-center">
                      😞 Review Needed
                    </h2>
                    <p className="text-orange-800 mb-6 text-lg text-center">
                      You've used all 3 attempts. It's time to learn more before trying again.
                    </p>

                    {learningResources && learningResources.length > 0 ? (
                      <>
                        <p className="text-orange-900 font-semibold mb-4 text-center">
                          Here are some resources to help you understand this topic better:
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-6">
                          {learningResources.map((resource, index) => (
                            <div
                              key={index}
                              className="bg-white rounded-lg p-4 border border-orange-200 hover:shadow-md transition-shadow"
                            >
                              <h3 className="font-semibold text-orange-900 mb-2 line-clamp-2">
                                {resource.title || 'Learning Resource'}
                              </h3>
                              {resource.summary && (
                                <p className="text-sm text-gray-700 mb-3 line-clamp-3">
                                  {resource.summary}
                                </p>
                              )}
                              {resource.url ? (
                                <a
                                  href={resource.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center text-sm font-semibold text-indigo-700 hover:text-indigo-900 underline"
                                >
                                  Open resource →
                                </a>
                              ) : (
                                <p className="text-sm text-gray-500">No direct link available</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </>
                    ) : (
                      <p className="text-sm text-orange-800 mb-6 text-center">
                        Review a related website article or textbook example about the topic, then return and try a new question.
                      </p>
                    )}

                    <div className="text-center">
                      <button
                        onClick={handleNextProblem}
                        className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition"
                      >
                        Back to new question
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* {message && (
                <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-4 rounded">
                  <p className="text-gray-800">{message}</p>
                </div>
              )} */}

              {finalAnswer && (
                <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4 rounded">
                  <p className="text-blue-900 font-semibold mb-2">Final answer revealed</p>
                  <p className="text-gray-800 whitespace-pre-wrap">{finalAnswer}</p>
                  <div className="mt-4 text-right">
                    <button
                      onClick={handleNextProblem}
                      className="inline-flex items-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition"
                    >
                      Try a new question
                    </button>
                  </div>
                </div>
              )}

              {!reviewMode && sessionId && !finalAnswer && (
                <>
                  <input
                    type="text"
                    value={attempt}
                    onChange={(e) => setAttempt(e.target.value)}
                    placeholder="Your answer..."
                    className="w-full mb-3 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    onKeyPress={(e) => e.key === 'Enter' && handleSubmitAttempt()}
                  />
                  <button
                    onClick={handleSubmitAttempt}
                    disabled={status === 'loading' || !attempt.trim()}
                    className="w-full bg-green-600 text-white py-2 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 transition"
                  >
                    {status === 'loading' ? 'Checking...' : 'Submit Answer'}
                  </button>
                </>
              )}
            </>
          ) : (
            <div className="relative overflow-hidden rounded-lg p-6 bg-gradient-to-br from-emerald-50 via-white to-lime-50 border border-emerald-200 mb-4">
              <div className="celebration-wrapper pointer-events-none">
                {Array.from({ length: 12 }).map((_, index) => (
                  <span
                    key={index}
                    className="confetti-piece"
                    style={{
                      left: `${8 + index * 7}%`,
                      animationDelay: `${index * 0.1}s`,
                      backgroundColor: ['#84cc16', '#22c55e', '#14b8a6', '#0ea5e9'][index % 4],
                    }}
                  />
                ))}
              </div>
              <div className="relative text-center">
                <h2 className="text-3xl font-bold text-emerald-900 mb-3">
                  🎉 Congratulations!
                </h2>
                <p className="text-gray-700 mb-6 text-lg">
                  {message ?? 'That was the right answer! Great job.'}
                </p>
                <button
                  onClick={handleNextProblem}
                  className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition"
                >
                  Next problem
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}
        </div>

        <div className="bg-indigo-50 rounded-lg p-4 text-center text-sm text-gray-600">
          <p>
            📚 StudyOwl uses Socratic questioning to help you learn, not spoil the answers!
          </p>
        </div>
      </div>
    </div>
  )
}

export default StudentChat
