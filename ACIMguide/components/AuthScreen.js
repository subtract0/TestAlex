import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Image
} from 'react-native';
import FirebaseService from '../services/FirebaseService';

const AuthScreen = ({ onAuthSuccess }) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleAnonymousSignIn = async () => {
    setIsLoading(true);
    try {
      const user = await FirebaseService.signInAnonymously();
      console.log('Anonymous sign-in successful:', user.uid);
      onAuthSuccess(user);
    } catch (error) {
      console.error('Sign-in error:', error);
      Alert.alert(
        'Sign-in Error',
        'Failed to sign in. Please check your connection and try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <View style={styles.logoContainer}>
          <Text style={styles.logoText}>🕊️</Text>
          <Text style={styles.title}>ACIMguide</Text>
          <Text style={styles.subtitle}>
            Your companion for A Course in Miracles
          </Text>
        </View>

        <View style={styles.descriptionContainer}>
          <Text style={styles.description}>
            Experience personalized guidance based on ACIM teachings. Get help with:
          </Text>
          
          <View style={styles.featureList}>
            <Text style={styles.feature}>• Forgiveness practices</Text>
            <Text style={styles.feature}>• Daily lesson insights</Text>
            <Text style={styles.feature}>• Inner peace cultivation</Text>
            <Text style={styles.feature}>• Relationship healing</Text>
          </View>
        </View>

        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={[styles.signInButton, isLoading && styles.disabledButton]}
            onPress={handleAnonymousSignIn}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.signInButtonText}>Begin Your Journey</Text>
            )}
          </TouchableOpacity>
          
          <Text style={styles.privacyText}>
            Your conversations are private and secure
          </Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
    justifyContent: 'center',
    alignItems: 'center'
  },
  content: {
    width: '90%',
    maxWidth: 400,
    alignItems: 'center'
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 40
  },
  logoText: {
    fontSize: 60,
    marginBottom: 16
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#2C3E50',
    marginBottom: 8
  },
  subtitle: {
    fontSize: 16,
    color: '#7F8C8D',
    textAlign: 'center',
    fontStyle: 'italic'
  },
  descriptionContainer: {
    marginBottom: 40
  },
  description: {
    fontSize: 16,
    color: '#34495E',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 20
  },
  featureList: {
    alignItems: 'flex-start'
  },
  feature: {
    fontSize: 14,
    color: '#7F8C8D',
    marginBottom: 8,
    lineHeight: 20
  },
  buttonContainer: {
    width: '100%',
    alignItems: 'center'
  },
  signInButton: {
    backgroundColor: '#3498DB',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 25,
    width: '100%',
    alignItems: 'center',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5
  },
  disabledButton: {
    backgroundColor: '#BDC3C7'
  },
  signInButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600'
  },
  privacyText: {
    fontSize: 12,
    color: '#95A5A6',
    textAlign: 'center'
  }
});

export default AuthScreen;
