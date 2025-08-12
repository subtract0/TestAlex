import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Dimensions
} from 'react-native';
import OfflineStorage from '../services/OfflineStorage';

const { width } = Dimensions.get('window');

const QuickActions = ({ onQuickAction }) => {
  const [quickActions, setQuickActions] = useState([]);

  useEffect(() => {
    loadQuickActions();
  }, []);

  const loadQuickActions = async () => {
    try {
      const actions = await OfflineStorage.getQuickActions();
      setQuickActions(actions);
    } catch (error) {
      console.error('Failed to load quick actions:', error);
    }
  };

  const handleQuickAction = async (action) => {
    try {
      // Increment usage count
      await OfflineStorage.incrementQuickActionUsage(action.id);
      
      // Trigger the action
      onQuickAction(action);
      
      // Reload to update order
      loadQuickActions();
    } catch (error) {
      console.error('Failed to handle quick action:', error);
    }
  };

  const getCategoryIcon = (category) => {
    const icons = {
      forgiveness: '🙏',
      lessons: '📖',
      peace: '☮️',
      relationships: '💝',
      ego: '🧠',
      default: '✨'
    };
    return icons[category] || icons.default;
  };

  const getCategoryColor = (category) => {
    const colors = {
      forgiveness: '#E74C3C',
      lessons: '#3498DB',
      peace: '#2ECC71',
      relationships: '#E91E63',
      ego: '#9B59B6',
      default: '#95A5A6'
    };
    return colors[category] || colors.default;
  };

  if (quickActions.length === 0) {
    return null;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Quick Actions</Text>
      <ScrollView 
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {quickActions.map((action) => (
          <TouchableOpacity
            key={action.id}
            style={[
              styles.actionButton,
              { borderColor: getCategoryColor(action.category) }
            ]}
            onPress={() => handleQuickAction(action)}
          >
            <Text style={styles.actionIcon}>
              {getCategoryIcon(action.category)}
            </Text>
            <Text style={styles.actionTitle} numberOfLines={2}>
              {action.title}
            </Text>
            {action.usage_count > 0 && (
              <View style={styles.usageBadge}>
                <Text style={styles.usageText}>{action.usage_count}</Text>
              </View>
            )}
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingVertical: 16,
    paddingHorizontal: 16,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2C3E50',
    marginBottom: 12,
  },
  scrollContent: {
    paddingRight: 16,
  },
  actionButton: {
    width: 120,
    height: 100,
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    borderWidth: 2,
    marginRight: 12,
    padding: 12,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.18,
    shadowRadius: 1.0,
    elevation: 1,
  },
  actionIcon: {
    fontSize: 24,
    marginBottom: 4,
  },
  actionTitle: {
    fontSize: 12,
    fontWeight: '500',
    color: '#34495E',
    textAlign: 'center',
    lineHeight: 16,
  },
  usageBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    backgroundColor: '#E74C3C',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
  },
  usageText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: 'bold',
  },
});

export default QuickActions;
