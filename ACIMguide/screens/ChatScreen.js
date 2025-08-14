import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  Alert,
  Text,
  TouchableOpacity,
  SafeAreaView
} from 'react-native';
import MessageItem from '../components/MessageItem';
import MessageInput from '../components/MessageInput';
import QuickActions from '../components/QuickActions';
import FirebaseService from '../services/FirebaseService';
import OfflineStorage from '../services/OfflineStorage';

const ChatScreen = ({ user, onSignOut }) => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const flatListRef = useRef(null);

  useEffect(() => {
    initializeChat();
    return () => {
      FirebaseService.unsubscribe();
    };
  }, []);

  const initializeChat = async () => {
    try {
      // Load cached messages first (for offline experience)
      const cachedMessages = await FirebaseService.getCachedMessages();
      setMessages(cachedMessages);

      // Set up real-time listener for new messages
      FirebaseService.listenToMessages((newMessages) => {
        setMessages(newMessages);
        scrollToBottom();
      });

      // Sync any pending offline messages
      await FirebaseService.syncOfflineMessages();

    } catch (error) {
      console.error('Failed to initialize chat:', error);
    }
  };

  const scrollToBottom = () => {
    if (flatListRef.current && messages.length > 0) {
      setTimeout(() => {
        flatListRef.current.scrollToEnd({ animated: true });
      }, 100);
    }
  };

  const handleSendMessage = async (message) => {
    setIsLoading(true);
    
    try {
      const result = await FirebaseService.sendMessage(message);
      
      // Update messages with the new user and assistant messages
      setMessages(prevMessages => [
        ...prevMessages,
        result.userMessage,
        result.assistantMessage
      ]);
      
      scrollToBottom();
      
    } catch (error) {
      console.error('Failed to send message:', error);
      
      let errorMessage = 'Failed to send message. ';
      if (error.message.includes('Rate limit')) {
        errorMessage += 'You\'re sending messages too quickly. Please wait a moment.';
      } else if (error.message.includes('Daily token limit')) {
        errorMessage += 'Daily usage limit reached. Please try again tomorrow.';
      } else if (error.message.includes('network')) {
        errorMessage += 'Check your internet connection.';
        setIsOnline(false);
      } else {
        errorMessage += 'Please try again.';
      }
      
      Alert.alert('Error', errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = async (action) => {
    await handleSendMessage(action.prompt);
  };

  const handleClearThread = () => {
    Alert.alert(
      'Clear Conversation',
      'This will delete all messages and start a fresh conversation. Are you sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              await FirebaseService.clearThread();
              setMessages([]);
            } catch (error) {
              Alert.alert('Error', 'Failed to clear conversation. Please try again.');
            }
          }
        }
      ]
    );
  };

  const renderMessage = ({ item, index }) => (
    <MessageItem 
      message={item} 
      isLast={index === messages.length - 1}
    />
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Text style={styles.emptyStateIcon}>🕊️</Text>
      <Text style={styles.emptyStateTitle}>Welcome to ACIMguide</Text>
      <Text style={styles.emptyStateSubtitle}>
        I'm here to help you explore A Course in Miracles.
        Ask me anything about forgiveness, inner peace, or ACIM teachings.
      </Text>
    </View>
  );

  const renderHeader = () => (
    <View style={styles.header}>
      <View style={styles.headerLeft}>
        <Text style={styles.headerTitle}>ACIMguide</Text>
        {!isOnline && (
          <Text style={styles.offlineIndicator}>Offline</Text>
        )}
      </View>
      
      <View style={styles.headerRight}>
        <TouchableOpacity 
          style={styles.headerButton}
          onPress={handleClearThread}
        >
          <Text style={styles.headerButtonText}>Clear</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.headerButton}
          onPress={onSignOut}
        >
          <Text style={styles.headerButtonText}>Sign Out</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      {renderHeader()}
      
      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(item, index) => item.id || `message-${index}`}
        contentContainerStyle={[
          styles.messagesList,
          messages.length === 0 && styles.emptyStateContainer
        ]}
        ListEmptyComponent={renderEmptyState}
        onContentSizeChange={scrollToBottom}
        onLayout={scrollToBottom}
      />
      
      <QuickActions onQuickAction={handleQuickAction} />
      
      <MessageInput
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2C3E50',
  },
  offlineIndicator: {
    fontSize: 12,
    color: '#E74C3C',
    marginLeft: 8,
    paddingHorizontal: 6,
    paddingVertical: 2,
    backgroundColor: '#FADBD8',
    borderRadius: 4,
  },
  headerRight: {
    flexDirection: 'row',
  },
  headerButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginLeft: 8,
  },
  headerButtonText: {
    color: '#3498DB',
    fontSize: 16,
    fontWeight: '500',
  },
  messagesList: {
    flexGrow: 1,
    paddingVertical: 8,
  },
  emptyStateContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    flex: 1,
  },
  emptyState: {
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  emptyStateIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyStateTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2C3E50',
    marginBottom: 12,
    textAlign: 'center',
  },
  emptyStateSubtitle: {
    fontSize: 16,
    color: '#7F8C8D',
    textAlign: 'center',
    lineHeight: 24,
  },
});

export default ChatScreen;
