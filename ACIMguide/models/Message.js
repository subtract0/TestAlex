export class Message {
  constructor({
    id = null,
    content = '',
    isUser = false,
    timestamp = Date.now(),
    status = 'sending',
    citations = [],
    userId = null,
    threadId = null
  }) {
    this.id = id;
    this.content = content;
    this.isUser = isUser;
    this.timestamp = timestamp;
    this.status = status; // 'sending', 'sent', 'delivered', 'failed'
    this.citations = citations;
    this.userId = userId;
    this.threadId = threadId;
  }

  static fromFirestore(doc) {
    const data = doc.data();
    return new Message({
      id: doc.id,
      content: data.assistantResponse || data.userMessage || '',
      isUser: data.userMessage ? !data.assistantResponse : false,
      timestamp: data.timestamp?.toDate?.() || data.timestamp || Date.now(),
      status: data.status || 'delivered',
      citations: data.citations || [],
      userId: data.userId,
      threadId: data.threadId
    });
  }
}

export class Citation {
  constructor({ text, source, page = null }) {
    this.text = text;
    this.source = source;
    this.page = page;
  }
}
