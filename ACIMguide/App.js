import React, { useState, useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, View, Alert } from 'react-native';
import AuthScreen from './components/AuthScreen';
import ChatScreen from './screens/ChatScreen';
import FirebaseService from './services/FirebaseService';
import OfflineStorage from './services/OfflineStorage';

export default function App() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Initialize offline storage
      await OfflineStorage.init();

      // Listen for auth state changes
      FirebaseService.onAuthStateChanged((user) => {
        setUser(user);
        setIsLoading(false);
      });
    } catch (error) {
      console.error('App initialization failed:', error);
      Alert.alert(
        'Initialization Error',
        'Failed to initialize the app. Please restart and try again.'
      );
      setIsLoading(false);
    }
  };

  const handleAuthSuccess = (user) => {
    setUser(user);
  };

  const handleSignOut = async () => {
    try {
      await FirebaseService.signOut();
      setUser(null);
    } catch (error) {
      console.error('Sign out failed:', error);
      Alert.alert('Error', 'Failed to sign out. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        {/* You could add a loading spinner here */}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar style="dark" backgroundColor="#FFFFFF" />
      
      {user ? (
        <ChatScreen user={user} onSignOut={handleSignOut} />
      ) : (
        <AuthScreen onAuthSuccess={handleAuthSuccess} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA'
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#F8F9FA',
    justifyContent: 'center',
    alignItems: 'center'
  }
});
