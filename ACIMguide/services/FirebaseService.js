import { 
  signInAnonymously, 
  signOut as firebaseSignOut,
  onAuthStateChanged 
} from 'firebase/auth';
import { 
  collection, 
  query, 
  where, 
  orderBy, 
  onSnapshot,
  addDoc,
  serverTimestamp,
  limit as firestoreLimit
} from 'firebase/firestore';
import { httpsCallable } from 'firebase/functions';
import { auth, firestore, functions } from '../config/firebase';
import { Message } from '../models/Message';
import OfflineStorage from './OfflineStorage';

class FirebaseService {
  constructor() {
    this.unsubscribeAuth = null;
    this.unsubscribeMessages = null;
    this.currentUser = null;
  }

  // Authentication methods
  async signInAnonymously() {
    try {
      const userCredential = await signInAnonymously(auth);
      this.currentUser = userCredential.user;
      return userCredential.user;
    } catch (error) {
      console.error('Anonymous sign-in failed:', error);
      throw error;
    }
  }

  async signOut() {
    try {
      await firebaseSignOut(auth);
      this.currentUser = null;
      
      // Clear local data
      await OfflineStorage.clearMessages();
    } catch (error) {
      console.error('Sign-out failed:', error);
      throw error;
    }
  }

  onAuthStateChanged(callback) {
    this.unsubscribeAuth = onAuthStateChanged(auth, (user) => {
      this.currentUser = user;
      callback(user);
    });
    return this.unsubscribeAuth;
  }

  // Chat methods
  async sendMessage(message, tone = 'gentle') {
    try {
      if (!this.currentUser) {
        throw new Error('User must be authenticated to send messages');
      }

      // Create user message object
      const userMessage = new Message({
        content: message,
        isUser: true,
        timestamp: Date.now(),
        status: 'sending',
        userId: this.currentUser.uid
      });

      // Save user message to local storage immediately
      await OfflineStorage.saveMessage(userMessage);

      // Call the cloud function
      const chatFunction = httpsCallable(functions, 'chatWithAssistant');
      const result = await chatFunction({ message, tone });

      const data = result.data;
      
      // Create assistant message from response
      const assistantMessage = new Message({
        id: data.messageId,
        content: data.response,
        isUser: false,
        timestamp: Date.now(),
        status: 'delivered',
        citations: data.citations || [],
        userId: this.currentUser.uid
      });

      // Save assistant message to local storage
      await OfflineStorage.saveMessage(assistantMessage);

      return {
        userMessage,
        assistantMessage,
        tokenUsage: {
          tokenIn: data.tokenIn,
          tokenOut: data.tokenOut,
          limitRemaining: data.limitRemaining
        }
      };

    } catch (error) {
      console.error('Send message failed:', error);
      
      // Update message status to failed
      const failedMessage = new Message({
        content: message,
        isUser: true,
        timestamp: Date.now(),
        status: 'failed',
        userId: this.currentUser?.uid
      });
      
      await OfflineStorage.saveMessage(failedMessage);
      throw error;
    }
  }

  async clearThread() {
    try {
      if (!this.currentUser) {
        throw new Error('User must be authenticated to clear thread');
      }

      const clearThreadFunction = httpsCallable(functions, 'clearThread');
      const result = await clearThreadFunction({});

      // Clear local messages
      await OfflineStorage.clearMessages();

      return result.data;
    } catch (error) {
      console.error('Clear thread failed:', error);
      throw error;
    }
  }

  // Listen to real-time message updates from Firestore
  listenToMessages(callback, messageLimit = 50) {
    if (!this.currentUser) {
      console.warn('No authenticated user for message listening');
      return null;
    }

    const messagesRef = collection(firestore, 'messages');
    const q = query(
      messagesRef,
      where('userId', '==', this.currentUser.uid),
      orderBy('timestamp', 'desc'),
      firestoreLimit(messageLimit)
    );

    this.unsubscribeMessages = onSnapshot(q, (snapshot) => {
      const messages = [];
      
      snapshot.forEach((doc) => {
        try {
          const message = Message.fromFirestore(doc);
          messages.push(message);
          
          // Also save to offline storage
          OfflineStorage.saveMessage(message);
        } catch (error) {
          console.error('Error processing message from Firestore:', error);
        }
      });

      // Sort messages chronologically
      messages.sort((a, b) => a.timestamp - b.timestamp);
      callback(messages);
    }, (error) => {
      console.error('Error listening to messages:', error);
      callback([]);
    });

    return this.unsubscribeMessages;
  }

  // Offline synchronization
  async syncOfflineMessages() {
    try {
      if (!this.currentUser) {
        return;
      }

      const unsyncedMessages = await OfflineStorage.getUnsyncedMessages();
      
      for (const message of unsyncedMessages) {
        if (message.isUser) {
          // Re-send user messages that weren't processed
          try {
            await this.sendMessage(message.content);
            await OfflineStorage.markMessageSynced(message.id);
          } catch (error) {
            console.error('Failed to sync user message:', error);
          }
        }
      }
    } catch (error) {
      console.error('Sync failed:', error);
    }
  }

  // Get cached messages from local storage
  async getCachedMessages() {
    try {
      if (!this.currentUser) {
        return [];
      }
      
      return await OfflineStorage.getMessages(this.currentUser.uid);
    } catch (error) {
      console.error('Failed to get cached messages:', error);
      return [];
    }
  }

  // Clean up listeners
  unsubscribe() {
    if (this.unsubscribeAuth) {
      this.unsubscribeAuth();
      this.unsubscribeAuth = null;
    }
    
    if (this.unsubscribeMessages) {
      this.unsubscribeMessages();
      this.unsubscribeMessages = null;
    }
  }

  getCurrentUser() {
    return this.currentUser;
  }
}

export default new FirebaseService();
