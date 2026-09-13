import { useState } from 'react'
import {
  MessageSquare,
  X,
  Sparkles,
  Maximize2,
  Minimize2,
} from 'lucide-react'
import { useWorkspace } from '../context/WorkspaceContext.jsx'
import ResearchPromptForm from '../features/research/ResearchPromptForm.jsx'

function FloatingResearchChat() {
  const [open, setOpen] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const { activeCompany, activeDocument } = useWorkspace()

  // Backend requires status === 'indexed'.
  const isReady =
    !!activeDocument &&
    activeDocument.status === 'indexed'

  const documentId = isReady
    ? activeDocument.document_id
    : null

  function handleClose() {
    setOpen(false)
    setExpanded(false)
  }

  function handleToggleExpand() {
    setExpanded((prev) => !prev)
  }

  return (
    <>
      {/* =========================================================
          FLOATING RESEARCH BUTTON
      ========================================================= */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={`fixed bottom-6 right-6 z-40
          w-14 h-14
          rounded-2xl
          bg-blue-600
          text-white
          flex items-center justify-center
          shadow-xl shadow-blue-600/25
          hover:bg-blue-700
          hover:scale-105
          active:scale-95
          transition-all duration-200
          ${
            open ? 'hidden' : ''
          }`}
        title="Research Agent"
        aria-label="Open Research Agent"
      >
        <MessageSquare size={22} />
      </button>

      {/* =========================================================
          RESEARCH CHAT WINDOW
      ========================================================= */}
      {open && (
        <div
          className={`
            fixed z-50
            flex flex-col
            overflow-hidden
            bg-white
            border border-slate-200
            shadow-[0_25px_80px_rgba(15,23,42,0.20)]
            animate-fadeIn
            transition-all duration-200

            ${
              expanded
                ? `
                  inset-3
                  sm:inset-4
                  lg:inset-5
                  rounded-2xl
                `
                : `
                  bottom-24
                  right-6
                  w-[26rem]
                  h-[36rem]
                  max-h-[80vh]
                  rounded-2xl
                `
            }
          `}
        >
          {/* =====================================================
              TOP HEADER
          ===================================================== */}
          <header
            className={`
              flex-shrink-0
              flex items-center justify-between
              bg-gradient-to-r from-blue-600 to-blue-700
              text-white
              border-b border-blue-500/40
              ${
                expanded
                  ? 'px-5 py-3.5'
                  : 'px-4 py-3'
              }
            `}
          >
            {/* LEFT */}
            <div className="flex items-center gap-3 min-w-0">
              <div
                className="
                  w-9 h-9
                  rounded-xl
                  bg-white/15
                  border border-white/15
                  flex items-center justify-center
                  flex-shrink-0
                "
              >
                <Sparkles size={17} />
              </div>

              <div className="min-w-0">
                <div
                  className="
                    flex items-center gap-2
                    text-sm font-extrabold
                    leading-tight
                  "
                >
                  <span>Research Agent</span>

                  {activeCompany && (
                    <span className="text-blue-100 font-semibold">
                      · {activeCompany.ticker || activeCompany.name}
                    </span>
                  )}
                </div>

                {expanded && (
                  <div className="text-[10px] text-blue-100 mt-0.5 font-medium">
                    Financial document research
                  </div>
                )}
              </div>
            </div>

            {/* RIGHT CONTROLS */}
            <div className="flex items-center gap-1 flex-shrink-0">
              <button
                type="button"
                onClick={handleToggleExpand}
                className="
                  w-8 h-8
                  rounded-lg
                  flex items-center justify-center
                  text-white/80
                  hover:text-white
                  hover:bg-white/10
                  transition-colors
                "
                title={
                  expanded
                    ? 'Exit maximize'
                    : 'Maximize'
                }
                aria-label={
                  expanded
                    ? 'Exit maximize'
                    : 'Maximize'
                }
              >
                {expanded ? (
                  <Minimize2 size={17} />
                ) : (
                  <Maximize2 size={17} />
                )}
              </button>

              <button
                type="button"
                onClick={handleClose}
                className="
                  w-8 h-8
                  rounded-lg
                  flex items-center justify-center
                  text-white/80
                  hover:text-white
                  hover:bg-white/10
                  transition-colors
                "
                title="Close"
                aria-label="Close Research Agent"
              >
                <X size={18} />
              </button>
            </div>
          </header>

          {/* =====================================================
              CONTENT
          ===================================================== */}
          <div className="flex-1 min-h-0 overflow-hidden bg-slate-50/60">
            {isReady ? (
              <ResearchPromptForm
                documentId={documentId}
                compact={!expanded}
              />
            ) : (
              <div className="h-full flex items-center justify-center p-6">
                <div
                  className="
                    max-w-md
                    text-center
                    bg-white
                    border border-slate-200
                    rounded-2xl
                    p-6
                    shadow-sm
                  "
                >
                  <div
                    className="
                      mx-auto mb-4
                      w-12 h-12
                      rounded-2xl
                      bg-amber-50
                      text-amber-600
                      flex items-center justify-center
                    "
                  >
                    <MessageSquare size={22} />
                  </div>

                  <h3 className="text-sm font-extrabold text-slate-900">
                    Research chat unavailable
                  </h3>

                  <p className="mt-2 text-xs leading-relaxed text-slate-500">
                    {activeCompany
                      ? "This company's document is still processing. Research chat will be available once it finishes indexing."
                      : 'Select a company with an uploaded, indexed document to start asking research questions.'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}

export default FloatingResearchChat