import * as SQLite from 'expo-sqlite';
import { Message } from '../models/Message';

class OfflineStorageService {
  constructor() {
    this.db = null;
  }

  async init() {
    try {
      this.db = await SQLite.openDatabaseAsync('acimguide.db');
      await this.createTables();
    } catch (error) {
      console.error('Failed to initialize database:', error);
    }
  }

  async createTables() {
    const createMessagesTable = `
      CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        isUser INTEGER NOT NULL,
        timestamp INTEGER NOT NULL,
        status TEXT DEFAULT 'delivered',
        citations TEXT,
        userId TEXT,
        threadId TEXT,
        synced INTEGER DEFAULT 0
      );
    `;

    const createSettingsTable = `
      CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
      );
    `;

    const createQuickActionsTable = `
      CREATE TABLE IF NOT EXISTS quick_actions (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        prompt TEXT NOT NULL,
        category TEXT,
        usage_count INTEGER DEFAULT 0
      );
    `;

    await this.db.execAsync(createMessagesTable);
    await this.db.execAsync(createSettingsTable);
    await this.db.execAsync(createQuickActionsTable);

    // Insert default quick actions
    await this.insertDefaultQuickActions();
  }

  async insertDefaultQuickActions() {
    const defaultActions = [
      {
        id: 'forgiveness-1',
        title: 'Help with Forgiveness',
        prompt: 'I need help practicing forgiveness in a difficult situation. Can you guide me through the ACIM approach?',
        category: 'forgiveness'
      },
      {
        id: 'daily-lesson',
        title: 'Today\'s Lesson Guidance',
        prompt: 'Can you help me understand and apply today\'s ACIM lesson?',
        category: 'lessons'
      },
      {
        id: 'peace-practice',
        title: 'Finding Inner Peace',
        prompt: 'I\'m feeling stressed and anxious. How can ACIM principles help me find peace?',
        category: 'peace'
      },
      {
        id: 'relationship-healing',
        title: 'Healing Relationships',
        prompt: 'I\'m having difficulties in my relationships. How does ACIM teach us to heal them?',
        category: 'relationships'
      },
      {
        id: 'ego-identification',
        title: 'Recognizing Ego',
        prompt: 'Help me identify when my ego is active and how to return to love.',
        category: 'ego'
      }
    ];

    for (const action of defaultActions) {
      try {
        await this.db.runAsync(
          'INSERT OR IGNORE INTO quick_actions (id, title, prompt, category, usage_count) VALUES (?, ?, ?, ?, ?)',
          [action.id, action.title, action.prompt, action.category, 0]
        );
      } catch (error) {
        console.log('Quick action already exists:', action.id);
      }
    }
  }

  async saveMessage(message) {
    try {
      await this.db.runAsync(
        'INSERT OR REPLACE INTO messages (id, content, isUser, timestamp, status, citations, userId, threadId, synced) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [
          message.id || `local_${Date.now()}_${Math.random()}`,
          message.content,
          message.isUser ? 1 : 0,
          message.timestamp,
          message.status,
          JSON.stringify(message.citations || []),
          message.userId,
          message.threadId,
          message.id ? 1 : 0 // If it has a Firestore ID, it's synced
        ]
      );
    } catch (error) {
      console.error('Failed to save message:', error);
    }
  }

  async getMessages(userId, limit = 50) {
    try {
      const result = await this.db.getAllAsync(
        'SELECT * FROM messages WHERE userId = ? ORDER BY timestamp DESC LIMIT ?',
        [userId, limit]
      );

      return result.map(row => new Message({
        id: row.id,
        content: row.content,
        isUser: row.isUser === 1,
        timestamp: row.timestamp,
        status: row.status,
        citations: JSON.parse(row.citations || '[]'),
        userId: row.userId,
        threadId: row.threadId
      })).reverse(); // Return in chronological order
    } catch (error) {
      console.error('Failed to get messages:', error);
      return [];
    }
  }

  async getUnsyncedMessages() {
    try {
      const result = await this.db.getAllAsync(
        'SELECT * FROM messages WHERE synced = 0'
      );
      return result.map(row => new Message({
        id: row.id,
        content: row.content,
        isUser: row.isUser === 1,
        timestamp: row.timestamp,
        status: row.status,
        citations: JSON.parse(row.citations || '[]'),
        userId: row.userId,
        threadId: row.threadId
      }));
    } catch (error) {
      console.error('Failed to get unsynced messages:', error);
      return [];
    }
  }

  async markMessageSynced(messageId) {
    try {
      await this.db.runAsync(
        'UPDATE messages SET synced = 1 WHERE id = ?',
        [messageId]
      );
    } catch (error) {
      console.error('Failed to mark message as synced:', error);
    }
  }

  async clearMessages() {
    try {
      await this.db.runAsync('DELETE FROM messages');
    } catch (error) {
      console.error('Failed to clear messages:', error);
    }
  }

  async saveSetting(key, value) {
    try {
      await this.db.runAsync(
        'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
        [key, JSON.stringify(value)]
      );
    } catch (error) {
      console.error('Failed to save setting:', error);
    }
  }

  async getSetting(key, defaultValue = null) {
    try {
      const result = await this.db.getFirstAsync(
        'SELECT value FROM settings WHERE key = ?',
        [key]
      );
      return result ? JSON.parse(result.value) : defaultValue;
    } catch (error) {
      console.error('Failed to get setting:', error);
      return defaultValue;
    }
  }

  async getQuickActions() {
    try {
      const result = await this.db.getAllAsync(
        'SELECT * FROM quick_actions ORDER BY usage_count DESC, title ASC'
      );
      return result;
    } catch (error) {
      console.error('Failed to get quick actions:', error);
      return [];
    }
  }

  async incrementQuickActionUsage(actionId) {
    try {
      await this.db.runAsync(
        'UPDATE quick_actions SET usage_count = usage_count + 1 WHERE id = ?',
        [actionId]
      );
    } catch (error) {
      console.error('Failed to increment quick action usage:', error);
    }
  }
}

export default new OfflineStorageService();
