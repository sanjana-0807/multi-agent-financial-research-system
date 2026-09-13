import { useState, useRef, useEffect } from 'react'
import {
  Send,
  Cpu,
  User,
  Sparkles,
  FileText,
  X,
  ExternalLink,
  AlertCircle,
  Loader2,
  Plus,
  MessageSquare,
  ChevronDown,
} from 'lucide-react'

import Button from '../../components/Button.jsx'
import useResearchChat from './useResearchChat.js'

const SUGGESTED_PROMPTS = [
  'What was total revenue in the most recent fiscal year?',
  "Who is the company's CEO?",
  'What is the percentage change in revenue year over year?',
  "Summarize the company's main business.",
]

function ResearchPromptForm({
  documentId,
  compact = false,
}) {
  const {
    messages,
    conversations,
    conversationId,
    sendQuestion,
    selectConversation,
    newChat,
    loading,
    loadingConversations,
    error,
  } = useResearchChat(documentId)

  const [prompt, setPrompt] = useState('')
  const [activeSource, setActiveSource] = useState(null)
  const [showConversations, setShowConversations] =
    useState(false)

  const scrollRef = useRef(null)

  /* ============================================================
     AUTO SCROLL
  ============================================================ */

  useEffect(() => {
    const element = scrollRef.current

    if (!element) {
      return
    }

    element.scrollTo({
      top: element.scrollHeight,
      behavior: 'smooth',
    })
  }, [messages, loading])

  /* ============================================================
     SUBMIT
  ============================================================ */

  function handleSubmit(e) {
    e.preventDefault()

    if (
      !prompt.trim() ||
      loading ||
      !documentId
    ) {
      return
    }

    sendQuestion(prompt)
    setPrompt('')
  }

  function handleSelectSuggested(text) {
    setPrompt(text)
  }

  /* ============================================================
     SELECT CHAT
  ============================================================ */

  async function handleSelectConversation(id) {
    if (loading) {
      return
    }

    await selectConversation(id)

    setShowConversations(false)
    setPrompt('')
  }

  /* ============================================================
     NEW CHAT
  ============================================================ */

  function handleNewChat() {
    if (loading) {
      return
    }

    newChat()
    setPrompt('')
    setShowConversations(false)
  }

  /* ============================================================
     CHAT LIST
  ============================================================ */

  function ConversationList({
    desktop = false,
  }) {
    return (
      <div
        className={`
          flex flex-col
          ${
            desktop
              ? 'h-full'
              : 'max-h-72'
          }
        `}
      >
        {/* LIST HEADER */}
        <div
          className="
            px-4 py-3
            border-b border-slate-100
            flex-shrink-0
          "
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-extrabold text-slate-900">
                Research Chats
              </p>

              <p className="text-[10px] text-slate-400 mt-0.5">
                Conversations for this document
              </p>
            </div>

            <span
              className="
                min-w-6 h-6 px-1.5
                rounded-lg
                bg-slate-100
                text-slate-500
                flex items-center justify-center
                text-[10px]
                font-bold
              "
            >
              {conversations.length}
            </span>
          </div>
        </div>

        {/* LIST */}
        <div
          className="
            flex-1
            min-h-0
            overflow-y-auto
            custom-scrollbar
          "
        >
          {loadingConversations &&
          conversations.length === 0 ? (
            <div className="h-32 flex items-center justify-center">
              <Loader2
                size={17}
                className="animate-spin text-blue-600"
              />
            </div>
          ) : conversations.length === 0 ? (
            <div
              className="
                px-5 py-10
                text-center
              "
            >
              <MessageSquare
                size={22}
                className="mx-auto text-slate-300"
              />

              <p className="mt-3 text-[11px] font-semibold text-slate-400">
                No saved chats yet.
              </p>

              <p className="mt-1 text-[10px] text-slate-400">
                Your first question will create a conversation.
              </p>
            </div>
          ) : (
            conversations.map((conversation) => {
              const isActive =
                conversation.conversation_id ===
                conversationId

              return (
                <button
                  key={
                    conversation.conversation_id
                  }
                  type="button"
                  onClick={() =>
                    handleSelectConversation(
                      conversation.conversation_id
                    )
                  }
                  className={`
                    w-full
                    text-left
                    px-4 py-3
                    border-b border-slate-100
                    transition-all
                    ${
                      isActive
                        ? `
                          bg-blue-50
                          border-l-2
                          border-l-blue-600
                        `
                        : `
                          bg-white
                          hover:bg-slate-50
                          border-l-2
                          border-l-transparent
                        `
                    }
                  `}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`
                        mt-0.5
                        w-7 h-7
                        rounded-lg
                        flex items-center justify-center
                        flex-shrink-0
                        ${
                          isActive
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-100 text-slate-400'
                        }
                      `}
                    >
                      <MessageSquare size={13} />
                    </div>

                    <div className="min-w-0 flex-1">
                      <p
                        className={`
                          text-xs
                          leading-snug
                          line-clamp-2
                          ${
                            isActive
                              ? 'font-bold text-blue-700'
                              : 'font-semibold text-slate-700'
                          }
                        `}
                      >
                        {conversation.title ||
                          'New Chat'}
                      </p>

                      {conversation.updated_at && (
                        <p className="text-[9px] font-medium text-slate-400 mt-1.5">
                          {new Date(
                            conversation.updated_at
                          ).toLocaleString()}
                        </p>
                      )}
                    </div>

                    {isActive && (
                      <span
                        className="
                          w-1.5 h-1.5
                          rounded-full
                          bg-blue-600
                          mt-2
                          flex-shrink-0
                        "
                      />
                    )}
                  </div>
                </button>
              )
            })
          )}
        </div>
      </div>
    )
  }

  return (
    <div
      className={`
        h-full
        flex
        overflow-hidden
        ${
          compact
            ? 'p-3 bg-slate-50/60'
            : 'bg-slate-50/80'
        }
      `}
    >
      {/* ========================================================
          MAXIMIZED LEFT SIDEBAR
      ======================================================== */}

      {!compact && (
        <aside
          className="
            w-64
            xl:w-72
            flex-shrink-0
            bg-white
            border border-slate-200
            rounded-2xl
            shadow-sm
            overflow-hidden
            flex flex-col
            mr-4
          "
        >
          {/* SIDEBAR TOP */}
          <div
            className="
              p-4
              border-b border-slate-100
              flex-shrink-0
            "
          >
            <button
              type="button"
              onClick={handleNewChat}
              disabled={loading}
              className="
                w-full
                flex items-center justify-center gap-2
                px-4 py-2.5
                rounded-xl
                bg-blue-600
                text-white
                text-xs font-bold
                shadow-sm shadow-blue-600/20
                hover:bg-blue-700
                transition-colors
                disabled:opacity-50
                disabled:cursor-not-allowed
              "
            >
              <Plus size={15} />
              New Chat
            </button>
          </div>

          {/* SIDEBAR LIST */}
          <div className="flex-1 min-h-0">
            <ConversationList desktop />
          </div>
        </aside>
      )}

      {/* ========================================================
          MAIN CHAT AREA
      ======================================================== */}

      <main
        className="
          flex-1
          min-w-0
          min-h-0
          flex flex-col
          overflow-hidden
        "
      >
        {/* ======================================================
            COMPACT CONTROLS
        ====================================================== */}

        {compact && documentId && (
          <div
            className="
              relative
              flex items-center
              gap-2
              flex-shrink-0
              mb-3
            "
          >
            <button
              type="button"
              onClick={handleNewChat}
              disabled={loading}
              className="
                flex items-center gap-1.5
                px-3 py-2
                rounded-xl
                bg-blue-600
                text-white
                text-xs font-bold
                hover:bg-blue-700
                transition-colors
                disabled:opacity-50
              "
            >
              <Plus size={14} />
              New Chat
            </button>

            <button
              type="button"
              onClick={() =>
                setShowConversations(
                  (prev) => !prev
                )
              }
              disabled={loadingConversations}
              className="
                flex items-center gap-1.5
                px-3 py-2
                rounded-xl
                bg-white
                border border-slate-200
                text-slate-700
                text-xs font-bold
                hover:border-blue-300
                hover:text-blue-600
                transition-colors
                disabled:opacity-50
              "
            >
              {loadingConversations ? (
                <Loader2
                  size={14}
                  className="animate-spin"
                />
              ) : (
                <MessageSquare size={14} />
              )}

              Chats

              {conversations.length > 0 && (
                <span
                  className="
                    min-w-5 h-5 px-1
                    rounded-full
                    bg-slate-100
                    text-slate-600
                    flex items-center justify-center
                    text-[10px]
                  "
                >
                  {conversations.length}
                </span>
              )}

              <ChevronDown
                size={12}
                className={`
                  transition-transform
                  ${
                    showConversations
                      ? 'rotate-180'
                      : ''
                  }
                `}
              />
            </button>

            {/* COMPACT CHAT DROPDOWN */}
            {showConversations && (
              <div
                className="
                  absolute
                  left-0
                  top-full
                  mt-2
                  z-40
                  w-[min(22rem,calc(100vw-2rem))]
                  bg-white
                  border border-slate-200
                  rounded-2xl
                  shadow-[0_20px_50px_rgba(15,23,42,0.15)]
                  overflow-hidden
                "
              >
                <ConversationList />
              </div>
            )}

            {conversationId && (
              <span
                className="
                  ml-auto
                  text-[10px]
                  font-semibold
                  text-slate-400
                  truncate
                  max-w-[35%]
                "
              >
                Active conversation
              </span>
            )}
          </div>
        )}

        {/* ======================================================
            MAXIMIZED CHAT TITLE
        ====================================================== */}

        {!compact && (
          <div
            className="
              flex items-center justify-between
              px-1 pb-3
              flex-shrink-0
            "
          >
            <div>
              <p
                className="
                  text-[10px]
                  uppercase
                  tracking-[0.16em]
                  font-bold
                  text-blue-600
                "
              >
                Financial Research
              </p>

              <h2
                className="
                  text-lg
                  font-extrabold
                  text-slate-900
                  tracking-tight
                  mt-0.5
                "
              >
                {conversationId
                  ? 'Research Conversation'
                  : 'Start a New Conversation'}
              </h2>
            </div>

            <div
              className="
                hidden sm:flex
                items-center gap-2
                px-3 py-1.5
                rounded-full
                bg-white
                border border-slate-200
                text-[10px]
                font-bold
                text-slate-500
                shadow-sm
              "
            >
              <span
                className={`
                  w-1.5 h-1.5
                  rounded-full
                  ${
                    loading
                      ? 'bg-amber-400 animate-pulse'
                      : 'bg-emerald-500'
                  }
                `}
              />

              {loading
                ? 'Researching'
                : 'RAG Search Active'}
            </div>
          </div>
        )}

        {/* ======================================================
            NO DOCUMENT
        ====================================================== */}

        {!documentId && (
          <div
            className="
              flex items-center gap-3
              bg-amber-50
              border border-amber-200
              text-amber-800
              text-xs font-semibold
              rounded-xl
              p-3
              flex-shrink-0
              mb-3
            "
          >
            <AlertCircle
              size={16}
              className="flex-shrink-0"
            />

            <span>
              Select an indexed document to start
              asking questions.
            </span>
          </div>
        )}

        {/* ======================================================
            MESSAGES
        ====================================================== */}

        <div
          ref={scrollRef}
          className={`
            flex-1
            min-h-0
            overflow-y-auto
            custom-scrollbar
            ${
              compact
                ? `
                  bg-white
                  rounded-2xl
                  border border-slate-200
                  p-3
                `
                : `
                  bg-white
                  rounded-2xl
                  border border-slate-200
                  shadow-sm
                  px-5
                  py-6
                  sm:px-8
                `
            }
          `}
        >
          <div
            className={`
              mx-auto
              w-full
              ${
                compact
                  ? 'max-w-full'
                  : 'max-w-4xl'
              }
              space-y-5
            `}
          >
            {/* EMPTY STATE */}
            {messages.length === 0 && (
              <div
                className="
                  min-h-full
                  flex items-center justify-center
                  text-center
                  py-16
                "
              >
                <div className="max-w-md">
                  <div
                    className="
                      mx-auto
                      w-14 h-14
                      rounded-2xl
                      bg-blue-50
                      border border-blue-100
                      text-blue-600
                      flex items-center justify-center
                    "
                  >
                    <Sparkles size={24} />
                  </div>

                  <h3
                    className="
                      mt-5
                      text-base
                      font-extrabold
                      text-slate-900
                    "
                  >
                    Ask your financial document
                  </h3>

                  <p
                    className="
                      mt-2
                      text-xs
                      leading-relaxed
                      text-slate-500
                    "
                  >
                    Ask about revenue, management,
                    business operations, financial
                    metrics, or other information
                    contained in the filing.
                  </p>
                </div>
              </div>
            )}

            {/* MESSAGES */}
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`
                  flex items-start gap-3
                  ${
                    msg.role === 'user'
                      ? 'justify-end'
                      : 'justify-start'
                  }
                `}
              >
                {/* AVATAR */}
                {msg.role !== 'user' && (
                  <div
                    className="
                      w-8 h-8
                      rounded-xl
                      bg-blue-600
                      text-white
                      flex items-center justify-center
                      flex-shrink-0
                      shadow-sm
                      shadow-blue-600/20
                    "
                  >
                    <Cpu size={16} />
                  </div>
                )}

                {/* MESSAGE */}
                <div
                  className={`
                    max-w-[88%]
                    sm:max-w-[78%]
                    ${
                      msg.role === 'user'
                        ? 'items-end'
                        : 'items-start'
                    }
                    flex flex-col
                  `}
                >
                  <div
                    className={`
                      px-4 py-3
                      rounded-2xl
                      ${
                        msg.role === 'user'
                          ? `
                            bg-blue-600
                            text-white
                            rounded-tr-md
                            shadow-sm
                          `
                          : msg.isError
                          ? `
                            bg-red-50
                            text-red-700
                            border border-red-200
                            rounded-tl-md
                          `
                          : `
                            bg-slate-50
                            text-slate-800
                            border border-slate-200
                            rounded-tl-md
                          `
                      }
                    `}
                  >
                    <div
                      className={`
                        text-[10px]
                        font-bold
                        uppercase
                        tracking-wider
                        mb-1.5
                        ${
                          msg.role === 'user'
                            ? 'text-blue-100'
                            : 'text-slate-400'
                        }
                      `}
                    >
                      {msg.role === 'user'
                        ? 'You'
                        : 'Research Agent'}
                    </div>

                    <p
                      className="
                        text-sm
                        leading-6
                        whitespace-pre-wrap
                      "
                    >
                      {msg.content}
                    </p>

                    {/* SOURCES */}
                    {msg.sources &&
                      msg.sources.length > 0 && (
                        <div
                          className="
                            mt-4
                            pt-3
                            border-t
                            border-slate-200/70
                          "
                        >
                          <div
                            className="
                              flex items-center gap-1.5
                              mb-2
                              text-[9px]
                              font-bold
                              uppercase
                              tracking-wider
                              text-slate-400
                            "
                          >
                            <FileText size={11} />
                            Sources
                          </div>

                          <div className="flex flex-wrap gap-1.5">
                            {msg.sources.map(
                              (src, sIdx) => (
                                <button
                                  key={sIdx}
                                  type="button"
                                  onClick={() =>
                                    setActiveSource(src)
                                  }
                                  className="
                                    inline-flex
                                    items-center gap-1.5
                                    px-2 py-1
                                    rounded-lg
                                    bg-white
                                    border border-slate-200
                                    text-[9px]
                                    font-bold
                                    text-blue-600
                                    hover:border-blue-300
                                    hover:bg-blue-50
                                    transition-colors
                                  "
                                >
                                  <FileText size={10} />

                                  <span className="max-w-[220px] truncate">
                                    {src.filename ||
                                      src.source ||
                                      'Source'}

                                    {src.page != null
                                      ? ` · Page ${src.page}`
                                      : ''}
                                  </span>

                                  <ExternalLink
                                    size={9}
                                  />
                                </button>
                              )
                            )}
                          </div>
                        </div>
                      )}
                  </div>
                </div>

                {/* USER AVATAR */}
                {msg.role === 'user' && (
                  <div
                    className="
                      w-8 h-8
                      rounded-xl
                      bg-slate-900
                      text-white
                      flex items-center justify-center
                      flex-shrink-0
                    "
                  >
                    <User size={16} />
                  </div>
                )}
              </div>
            ))}

            {/* LOADING */}
            {loading && (
              <div className="flex items-start gap-3">
                <div
                  className="
                    w-8 h-8
                    rounded-xl
                    bg-blue-600
                    text-white
                    flex items-center justify-center
                    flex-shrink-0
                  "
                >
                  <Cpu size={16} />
                </div>

                <div
                  className="
                    flex items-center gap-2
                    px-4 py-3
                    rounded-2xl
                    rounded-tl-md
                    bg-slate-50
                    border border-slate-200
                    text-xs
                    font-semibold
                    text-slate-500
                  "
                >
                  <Loader2
                    size={14}
                    className="animate-spin text-blue-600"
                  />

                  Researching the document…
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ======================================================
            ERROR
        ====================================================== */}

        {error && (
          <div
            className="
              mt-2
              px-1
              text-[11px]
              font-semibold
              text-red-600
              flex-shrink-0
            "
          >
            {error}
          </div>
        )}

        {/* ======================================================
            SUGGESTED PROMPTS
        ====================================================== */}

        {(!compact || messages.length === 0) && (
          <div
            className="
              flex-shrink-0
              pt-3
            "
          >
            <div
              className="
                flex items-center gap-2
                overflow-x-auto
                custom-scrollbar
                pb-1
              "
            >
              <span
                className="
                  text-[9px]
                  font-bold
                  uppercase
                  tracking-wider
                  text-slate-400
                  flex-shrink-0
                "
              >
                Suggested
              </span>

              {SUGGESTED_PROMPTS.map(
                (txt, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() =>
                      handleSelectSuggested(txt)
                    }
                    className="
                      flex-shrink-0
                      px-3 py-1.5
                      rounded-full
                      bg-white
                      border border-slate-200
                      text-[10px]
                      font-semibold
                      text-slate-600
                      hover:border-blue-300
                      hover:text-blue-600
                      hover:bg-blue-50
                      transition-all
                    "
                  >
                    {txt}
                  </button>
                )
              )}
            </div>
          </div>
        )}

        {/* ======================================================
            INPUT
        ====================================================== */}

        <form
          onSubmit={handleSubmit}
          className="
            mt-2
            flex-shrink-0
          "
        >
          <div
            className="
              flex items-end gap-2
              bg-white
              border border-slate-200
              rounded-2xl
              shadow-sm
              focus-within:border-blue-300
              focus-within:ring-4
              focus-within:ring-blue-500/5
              transition-all
              p-2
            "
          >
            <textarea
              value={prompt}
              onChange={(e) =>
                setPrompt(e.target.value)
              }
              onKeyDown={(e) => {
                if (
                  e.key === 'Enter' &&
                  !e.shiftKey
                ) {
                  e.preventDefault()

                  if (
                    prompt.trim() &&
                    !loading &&
                    documentId
                  ) {
                    handleSubmit(e)
                  }
                }
              }}
              rows={1}
              disabled={!documentId || loading}
              placeholder={
                documentId
                  ? 'Ask a question about this document…'
                  : 'Select an indexed document first…'
              }
              className="
                flex-1
                min-h-[42px]
                max-h-32
                text-sm
                font-medium
                text-slate-800
                placeholder-slate-400
                bg-transparent
                resize-none
                outline-none
                py-2.5
                px-3
                disabled:cursor-not-allowed
              "
            />

            <button
              type="submit"
              disabled={
                !prompt.trim() ||
                loading ||
                !documentId
              }
              className="
                h-10
                px-4
                rounded-xl
                bg-blue-600
                text-white
                flex items-center
                justify-center
                gap-2
                text-xs
                font-bold
                shadow-sm
                shadow-blue-600/20
                hover:bg-blue-700
                active:scale-[0.98]
                transition-all
                disabled:opacity-40
                disabled:cursor-not-allowed
                flex-shrink-0
              "
            >
              <Send size={15} />
              <span className="hidden sm:inline">
                Send
              </span>
            </button>
          </div>

          <p
            className="
              text-[9px]
              text-slate-400
              text-center
              mt-1.5
              hidden sm:block
            "
          >
            Enter to send · Shift + Enter for a new line
          </p>
        </form>
      </main>

      {/* ========================================================
          SOURCE DETAIL MODAL
      ======================================================== */}

      {activeSource && (
        <div
          className="
            fixed inset-0
            z-[60]
            flex items-center justify-center
            p-4
            bg-slate-950/40
            backdrop-blur-sm
            animate-fadeIn
          "
          onClick={() =>
            setActiveSource(null)
          }
        >
          <div
            className="
              relative
              w-full
              max-w-lg
              bg-white
              rounded-2xl
              border border-slate-200
              shadow-2xl
              p-6
              animate-scaleUp
            "
            onClick={(e) =>
              e.stopPropagation()
            }
          >
            {/* MODAL HEADER */}
            <div
              className="
                flex items-center justify-between
                pb-3
                mb-4
                border-b border-slate-100
              "
            >
              <div className="flex items-center gap-2">
                <div
                  className="
                    w-8 h-8
                    rounded-lg
                    bg-blue-50
                    text-blue-600
                    flex items-center justify-center
                  "
                >
                  <FileText size={16} />
                </div>

                <div>
                  <h3 className="text-sm font-extrabold text-slate-900">
                    Source Detail
                  </h3>

                  <p className="text-[9px] text-slate-400 mt-0.5">
                    Research evidence
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() =>
                  setActiveSource(null)
                }
                className="
                  w-8 h-8
                  rounded-lg
                  flex items-center justify-center
                  text-slate-400
                  hover:text-slate-700
                  hover:bg-slate-100
                  transition-colors
                "
              >
                <X size={17} />
              </button>
            </div>

            {/* DETAILS */}
            <div className="space-y-3 text-xs">
              {activeSource.filename && (
                <div
                  className="
                    flex items-start
                    justify-between gap-5
                    p-3
                    rounded-xl
                    bg-slate-50
                  "
                >
                  <span
                    className="
                      text-[9px]
                      text-slate-400
                      font-bold
                      uppercase
                      tracking-wider
                    "
                  >
                    Filename
                  </span>

                  <span
                    className="
                      text-right
                      text-slate-700
                      font-semibold
                      break-all
                    "
                  >
                    {activeSource.filename}
                  </span>
                </div>
              )}

              {activeSource.page != null && (
                <div
                  className="
                    flex items-center
                    justify-between
                    p-3
                    rounded-xl
                    bg-slate-50
                  "
                >
                  <span
                    className="
                      text-[9px]
                      text-slate-400
                      font-bold
                      uppercase
                      tracking-wider
                    "
                  >
                    Page
                  </span>

                  <span className="font-bold text-slate-700">
                    {activeSource.page}
                  </span>
                </div>
              )}

              {activeSource.chunk_index != null && (
                <div
                  className="
                    flex items-center
                    justify-between
                    p-3
                    rounded-xl
                    bg-slate-50
                  "
                >
                  <span
                    className="
                      text-[9px]
                      text-slate-400
                      font-bold
                      uppercase
                      tracking-wider
                    "
                  >
                    Chunk
                  </span>

                  <span className="font-bold text-slate-700">
                    {activeSource.chunk_index}
                  </span>
                </div>
              )}

              {activeSource.source && (
                <div
                  className="
                    p-3
                    rounded-xl
                    bg-slate-50
                  "
                >
                  <span
                    className="
                      block
                      text-[9px]
                      text-slate-400
                      font-bold
                      uppercase
                      tracking-wider
                      mb-1
                    "
                  >
                    Source
                  </span>

                  <span
                    className="
                      block
                      text-slate-700
                      font-medium
                      break-all
                    "
                  >
                    {activeSource.source}
                  </span>
                </div>
              )}
            </div>

            {/* CLOSE */}
            <div className="flex justify-end mt-5">
              <button
                type="button"
                onClick={() =>
                  setActiveSource(null)
                }
                className="
                  px-4 py-2
                  bg-slate-900
                  text-white
                  text-xs
                  font-bold
                  rounded-xl
                  hover:bg-slate-800
                  transition-colors
                "
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ResearchPromptForm