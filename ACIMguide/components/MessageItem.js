import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Linking
} from 'react-native';

const MessageItem = ({ message, isLast = false }) => {
  const [showCitations, setShowCitations] = useState(false);

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleCitationPress = (citation) => {
    // You could implement navigation to the citation source here
    console.log('Citation pressed:', citation);
  };

  const renderContent = () => {
    // Handle message content with potential markdown-like formatting
    const content = message.content || '';
    
    // Simple formatting: make text between ** bold (for ACIM quotes)
    const parts = content.split(/(\*\*.*?\*\*)/g);
    
    return (
      <Text style={[styles.messageText, message.isUser && styles.userMessageText]}>
        {parts.map((part, index) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return (
              <Text key={index} style={styles.boldText}>
                {part.slice(2, -2)}
              </Text>
            );
          }
          return part;
        })}
      </Text>
    );
  };

  const renderCitations = () => {
    if (!message.citations || message.citations.length === 0) {
      return null;
    }

    return (
      <View style={styles.citationsContainer}>
        <TouchableOpacity
          style={styles.citationsToggle}
          onPress={() => setShowCitations(!showCitations)}
        >
          <Text style={styles.citationsToggleText}>
            📚 {message.citations.length} source{message.citations.length > 1 ? 's' : ''}
            {showCitations ? ' ↑' : ' ↓'}
          </Text>
        </TouchableOpacity>
        
        {showCitations && (
          <View style={styles.citationsList}>
            {message.citations.map((citation, index) => (
              <TouchableOpacity
                key={index}
                style={styles.citationItem}
                onPress={() => handleCitationPress(citation)}
              >
                <Text style={styles.citationText} numberOfLines={2}>
                  "{citation.text}"
                </Text>
                <Text style={styles.citationSource}>
                  — {citation.source}{citation.page ? `, p. ${citation.page}` : ''}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </View>
    );
  };

  const getStatusIcon = () => {
    switch (message.status) {
      case 'sending':
        return '⏳';
      case 'sent':
        return '✓';
      case 'delivered':
        return '✓✓';
      case 'failed':
        return '❌';
      default:
        return '';
    }
  };

  return (
    <View style={[
      styles.container,
      message.isUser ? styles.userContainer : styles.assistantContainer,
      isLast && styles.lastMessage
    ]}>
      <View style={[
        styles.messageBubble,
        message.isUser ? styles.userBubble : styles.assistantBubble
      ]}>
        {!message.isUser && (
          <Text style={styles.assistantLabel}>ACIMguide</Text>
        )}
        
        {renderContent()}
        
        <View style={styles.messageFooter}>
          <Text style={[
            styles.timestamp,
            message.isUser && styles.userTimestamp
          ]}>
            {formatTime(message.timestamp)}
          </Text>
          
          {message.isUser && (
            <Text style={styles.statusIcon}>
              {getStatusIcon()}
            </Text>
          )}
        </View>
        
        {renderCitations()}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 4,
    paddingHorizontal: 16,
  },
  lastMessage: {
    marginBottom: 16,
  },
  userContainer: {
    alignItems: 'flex-end',
  },
  assistantContainer: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 18,
  },
  userBubble: {
    backgroundColor: '#3498DB',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#FFFFFF',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  assistantLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#7F8C8D',
    marginBottom: 4,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
    color: '#2C3E50',
  },
  userMessageText: {
    color: '#FFFFFF',
  },
  boldText: {
    fontWeight: 'bold',
    fontStyle: 'italic',
  },
  messageFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  timestamp: {
    fontSize: 12,
    color: '#95A5A6',
  },
  userTimestamp: {
    color: 'rgba(255, 255, 255, 0.7)',
  },
  statusIcon: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    marginLeft: 4,
  },
  citationsContainer: {
    marginTop: 12,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#ECF0F1',
  },
  citationsToggle: {
    paddingVertical: 4,
  },
  citationsToggleText: {
    fontSize: 12,
    color: '#7F8C8D',
    fontWeight: '500',
  },
  citationsList: {
    marginTop: 8,
  },
  citationItem: {
    paddingVertical: 6,
    paddingHorizontal: 8,
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    marginBottom: 4,
  },
  citationText: {
    fontSize: 12,
    color: '#34495E',
    fontStyle: 'italic',
    lineHeight: 16,
  },
  citationSource: {
    fontSize: 10,
    color: '#7F8C8D',
    marginTop: 2,
    fontWeight: '500',
  },
});

export default MessageItem;
