import axiosClient from './axiosClient.js'

// Matches backend/routes/research.py
//
// POST /research/ask     -> synchronous Q&A over one indexed document.
//                            Returns { document_id, question, answer,
//                            conversation_id, sources } directly — there is
//                            no job/polling model for this endpoint.
// POST /research/redflag -> kept for callers still using it directly
//                            (note: currently returns 410, since red-flag
//                            analysis has moved to the Red Flag Agent /
//                            routes/red_flag.py).

/**
 * @param {Object} params
 * @param {string} params.documentId
 * @param {string} params.question
 * @param {string|null} [params.conversationId]
 * @param {{role: string, content: string}[]} [params.chatHistory]
 */
export function askResearch({
  documentId,
  question,
  conversationId = null,
  chatHistory = [],
}) {
  return axiosClient.post('/research/ask', {
    document_id: documentId,
    question,
    conversation_id: conversationId,
    chat_history: chatHistory.map(({ role, content }) => ({
      role,
      content,
    })),
  })
}

/**
 * Load all saved research conversations for one document.
 *
 * GET /research/conversations/{document_id}
 */
export function getResearchConversations(documentId) {
  return axiosClient.get(
    `/research/conversations/${documentId}`
  )
}

/**
 * Load all messages for one saved research conversation.
 *
 * GET /research/conversations/{conversation_id}/messages
 */
export function getResearchConversationMessages(
  conversationId,
  documentId
) {
  return axiosClient.get(
    `/research/conversations/${conversationId}/messages`,
    {
      params: {
        document_id: documentId,
      },
    }
  )
}

export function getRedFlagAnalysis(documentId) {
  return axiosClient.post(
    '/research/redflag',
    { document_id: documentId }
  )
}