import {
  useState,
  useCallback,
  useEffect,
  useRef,
} from 'react'

import {
  askResearch,
  getResearchConversations,
  getResearchConversationMessages,
} from '../../api/researchApi.js'

// Hook: manages multiple saved research chat conversations against one indexed
// document, backed by the synchronous POST /research/ask endpoint.
//
// Each assistant message carries `sources`, an array of
// { filename, page, chunk_index, source } as returned by the backend.
function useResearchChat(documentId) {
  const [messages, setMessages] = useState([])
  const [conversations, setConversations] = useState([])
  const [conversationId, setConversationId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingConversations, setLoadingConversations] = useState(false)
  const [error, setError] = useState(null)

  // Prevent an older request from overwriting newer conversation/document state.
  const requestIdRef = useRef(0)

  // ============================================================
  // LOAD CONVERSATION LIST
  // ============================================================

  const loadConversations = useCallback(async () => {
    if (!documentId) {
      setConversations([])
      return
    }

    const requestId = ++requestIdRef.current

    setLoadingConversations(true)
    setError(null)

    try {
      const res = await getResearchConversations(documentId)

      if (requestId !== requestIdRef.current) {
        return
      }

      const items = res.data?.conversations || []

      setConversations(items)
    } catch (err) {
      if (requestId !== requestIdRef.current) {
        return
      }

      const message =
        err.response?.data?.detail ||
        'Failed to load research chat history.'

      setError(message)
      setConversations([])
    } finally {
      if (requestId === requestIdRef.current) {
        setLoadingConversations(false)
      }
    }
  }, [documentId])

  // ============================================================
  // DOCUMENT CHANGE
  // ============================================================

  useEffect(() => {
    requestIdRef.current += 1

    setMessages([])
    setConversationId(null)
    setConversations([])
    setError(null)
    setLoading(false)

    if (documentId) {
      loadConversations()
    }
  }, [documentId, loadConversations])

  // ============================================================
  // LOAD ONE EXISTING CONVERSATION
  // ============================================================

  const selectConversation = useCallback(
    async (selectedConversationId) => {
      if (!selectedConversationId || !documentId) {
        return
      }

      if (
        selectedConversationId === conversationId &&
        messages.length > 0
      ) {
        return
      }

      const requestId = ++requestIdRef.current

      setError(null)
      setLoadingConversations(true)

      try {
        const res = await getResearchConversationMessages(
          selectedConversationId,
          documentId
        )

        if (requestId !== requestIdRef.current) {
          return
        }

        const loadedMessages = (
          res.data?.messages || []
        ).map((message) => ({
          role: message.role,
          content: message.content,
          sources: message.sources || [],
          created_at: message.created_at,
        }))

        setConversationId(
          res.data?.conversation_id ||
            selectedConversationId
        )

        setMessages(loadedMessages)
      } catch (err) {
        if (requestId !== requestIdRef.current) {
          return
        }

        const message =
          err.response?.data?.detail ||
          'Failed to load this research conversation.'

        setError(message)
      } finally {
        if (requestId === requestIdRef.current) {
          setLoadingConversations(false)
        }
      }
    },
    [
      documentId,
      conversationId,
      messages.length,
    ]
  )

  // ============================================================
  // NEW CHAT
  // ============================================================

  const newChat = useCallback(() => {
    requestIdRef.current += 1

    setMessages([])
    setConversationId(null)
    setError(null)
    setLoading(false)
    setLoadingConversations(false)
  }, [])

  // ============================================================
  // SEND QUESTION
  // ============================================================

  const sendQuestion = useCallback(
    async (question) => {
      const trimmed = (question || '').trim()

      if (
        !trimmed ||
        !documentId ||
        loading
      ) {
        return
      }

      setError(null)
      setLoading(true)

      // Preserve the existing chat history fallback.
      const historyForRequest = messages.map(
        ({ role, content }) => ({
          role,
          content,
        })
      )

      // Immediately display the user's question.
      setMessages((prev) => [
        ...prev,
        {
          role: 'user',
          content: trimmed,
        },
      ])

      try {
        const res = await askResearch({
          documentId,
          question: trimmed,
          conversationId,
          chatHistory: historyForRequest,
        })

        const {
          answer,
          conversation_id: newConversationId,
          sources,
        } = res.data

        const finalConversationId =
          newConversationId || conversationId

        setConversationId(finalConversationId)

        // Display assistant answer immediately.
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: answer,
            sources: sources || [],
          },
        ])

        // Refresh the saved conversation list.
        //
        // This makes a newly-created conversation appear in
        // the Chats list immediately.
        try {
          const conversationsRes =
            await getResearchConversations(
              documentId
            )

          const items =
            conversationsRes.data?.conversations ||
            []

          setConversations(items)
        } catch {
          // The research answer succeeded.
          // A history refresh failure should not
          // make the answer appear to have failed.
        }
      } catch (err) {
        const message =
          err.response?.data?.detail ||
          'Failed to get a research answer. Please try again.'

        setError(message)

        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: message,
            isError: true,
          },
        ])
      } finally {
        setLoading(false)
      }
    },
    [
      documentId,
      conversationId,
      messages,
      loading,
    ]
  )

  // ============================================================
  // RESET
  // ============================================================

  function reset() {
    newChat()
  }

  return {
    messages,
    conversations,
    conversationId,

    sendQuestion,
    selectConversation,
    newChat,
    loadConversations,

    loading,
    loadingConversations,
    error,

    reset,
  }
}

export default useResearchChat