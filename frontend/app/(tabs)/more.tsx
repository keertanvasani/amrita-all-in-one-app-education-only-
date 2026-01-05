import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

export default function MoreScreen() {
  const router = useRouter();

  const menuItems = [
    {
      id: 'results',
      title: 'Exam Scores',
      icon: 'stats-chart',
      color: '#ff9800',
      route: '/results',
    },
    {
      id: 'fees',
      title: 'Fee Payment',
      icon: 'card',
      color: '#4caf50',
      route: '/fees',
    },
    {
      id: 'registration',
      title: 'Course Registration',
      icon: 'clipboard',
      color: '#e91e63',
      route: '/registration',
    },
    {
      id: 'notifications',
      title: 'Notifications',
      icon: 'notifications',
      color: '#9c27b0',
      route: '/notifications',
    },
    {
      id: 'announcements',
      title: 'Announcements',
      icon: 'megaphone',
      color: '#f44336',
      route: '/announcements',
    },
    {
      id: 'settings',
      title: 'Settings',
      icon: 'settings',
      color: '#607d8b',
      route: '/settings',
    },
    {
      id: 'help',
      title: 'Help & Support',
      icon: 'help-circle',
      color: '#00bcd4',
      route: '/help',
    },
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>More</Text>
      </View>

      <View style={styles.menuGrid}>
        {menuItems.map((item) => (
          <TouchableOpacity
            key={item.id}
            style={styles.menuItem}
            onPress={() => router.push(item.route as any)}
          >
            <View style={[styles.iconContainer, { backgroundColor: `${item.color}20` }]}>
              <Ionicons name={item.icon as any} size={28} color={item.color} />
            </View>
            <Text style={styles.menuTitle}>{item.title}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.footer}>
        <Text style={styles.appName}>Student Portal</Text>
        <Text style={styles.version}>Version 1.0.0</Text>
        <Text style={styles.copyright}>
          © 2025 Amrita Vishwa Vidyapeetham
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#fff',
    paddingTop: 60,
    paddingBottom: 20,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
  },
  menuGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
  },
  menuItem: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    margin: '1%',
    alignItems: 'center',
    minHeight: 120,
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  iconContainer: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  menuTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    textAlign: 'center',
  },
  footer: {
    alignItems: 'center',
    padding: 32,
  },
  appName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  version: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  copyright: {
    fontSize: 12,
    color: '#999',
    marginTop: 8,
  },
});
