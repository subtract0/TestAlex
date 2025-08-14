import React, { useState } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Text,
  ActivityIndicator
} from 'react-native';

const MessageInput = ({ onSendMessage, isLoading = false, placeholder = "Ask ACIMguide anything..." }) => {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const isDisabled = !message.trim() || isLoading;

  return (
    <View style={styles.container}>
      <View style={styles.inputContainer}>
        <TextInput
          style={[styles.textInput, isLoading && styles.disabledInput]}
          value={message}
          onChangeText={setMessage}
          placeholder={placeholder}
          placeholderTextColor="#95A5A6"
          multiline
          maxLength={2000}
          editable={!isLoading}
          onSubmitEditing={handleSend}
          returnKeyType="send"
        />
        
        <TouchableOpacity
          style={[
            styles.sendButton,
            isDisabled && styles.disabledButton
          ]}
          onPress={handleSend}
          disabled={isDisabled}
        >
          {isLoading ? (
            <ActivityIndicator color="#FFFFFF" size="small" />
          ) : (
            <Text style={styles.sendIcon}>➤</Text>
          )}
        </TouchableOpacity>
      </View>
      
      {message.length > 1800 && (
        <Text style={styles.characterCount}>
          {message.length}/2000
        </Text>
      )}
      
      {isLoading && (
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>ACIMguide is thinking...</Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: '#F8F9FA',
    borderRadius: 25,
    paddingHorizontal: 16,
    paddingVertical: 8,
    minHeight: 50,
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    color: '#2C3E50',
    maxHeight: 100,
    paddingVertical: 8,
    paddingRight: 12,
  },
  disabledInput: {
    color: '#95A5A6',
  },
  sendButton: {
    backgroundColor: '#3498DB',
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
  },
  disabledButton: {
    backgroundColor: '#BDC3C7',
  },
  sendIcon: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  characterCount: {
    fontSize: 12,
    color: '#E74C3C',
    textAlign: 'right',
    marginTop: 4,
  },
  loadingContainer: {
    paddingVertical: 8,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 14,
    color: '#7F8C8D',
    fontStyle: 'italic',
  },
});

export default MessageInput;
