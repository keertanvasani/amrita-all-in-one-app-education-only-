import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useAuth } from '../../contexts/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import api from '../../utils/api';
import { useRouter } from 'expo-router';
import { format } from 'date-fns';

export default function HomeScreen() {
  const { user } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [dashboard, setDashboard] = useState<any>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const response = await api.get('/dashboard');
      setDashboard(response.data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadDashboard();
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0066cc" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Hello, {user?.name}!</Text>
          <Text style={styles.date}>{format(new Date(), 'EEEE, MMMM d, yyyy')}</Text>
        </View>
        <Ionicons name="notifications-outline" size={28} color="#333" />
      </View>

      <View style={styles.quickAccessGrid}>
        <TouchableOpacity
          style={[styles.tile, { backgroundColor: '#e3f2fd' }]}
          onPress={() => router.push('/courses')}
        >
          <Ionicons name="book" size={32} color="#0066cc" />
          <Text style={styles.tileTitle}>Courses</Text>
          <Text style={styles.tileSubtitle}>View all courses</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tile, { backgroundColor: '#fff3e0' }]}
          onPress={() => router.push('/results')}
        >
          <Ionicons name="stats-chart" size={32} color="#ff9800" />
          <Text style={styles.tileTitle}>Exam Scores</Text>
          <Text style={styles.tileSubtitle}>View results</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tile, { backgroundColor: '#e8f5e9' }]}
          onPress={() => router.push('/fees')}
        >
          <Ionicons name="card" size={32} color="#4caf50" />
          <Text style={styles.tileTitle}>Fee Payment</Text>
          {dashboard?.stats?.fee_due > 0 && (
            <Text style={styles.tileBadge}>₹{dashboard.stats.fee_due}</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tile, { backgroundColor: '#fce4ec' }]}
          onPress={() => router.push('/registration')}
        >
          <Ionicons name="clipboard" size={32} color="#e91e63" />
          <Text style={styles.tileTitle}>Registration</Text>
          <Text style={styles.tileSubtitle}>Course registration</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Ionicons name="document-text" size={24} color="#0066cc" />
          <Text style={styles.statNumber}>{dashboard?.stats?.pending_assignments || 0}</Text>
          <Text style={styles.statLabel}>Pending Assignments</Text>
        </View>

        <View style={styles.statCard}>
          <Ionicons name="checkmark-circle" size={24} color="#4caf50" />
          <Text style={styles.statNumber}>{dashboard?.stats?.upcoming_quizzes || 0}</Text>
          <Text style={styles.statLabel}>Upcoming Quizzes</Text>
        </View>
      </View>

      {dashboard?.announcements && dashboard.announcements.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Announcements</Text>
          {dashboard.announcements.map((announcement: any, index: number) => (
            <View key={index} style={styles.announcementCard}>
              <View style={styles.announcementHeader}>
                <Ionicons
                  name={announcement.priority === 'high' ? 'megaphone' : 'information-circle'}
                  size={20}
                  color={announcement.priority === 'high' ? '#f44336' : '#0066cc'}
                />
                <Text style={styles.announcementTitle}>{announcement.title}</Text>
              </View>
              <Text style={styles.announcementMessage}>{announcement.message}</Text>
              <Text style={styles.announcementDate}>
                {format(new Date(announcement.created_at), 'MMM d, yyyy')}
              </Text>
            </View>
          ))}
        </View>
      )}

      <View style={styles.motdContainer}>
        <Ionicons name="bulb" size={24} color="#ff9800" />
        <Text style={styles.motdText}>
          "Success is not final, failure is not fatal: it is the courage to continue that counts."
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 60,
    backgroundColor: '#fff',
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  date: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  quickAccessGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
  },
  tile: {
    width: '48%',
    margin: '1%',
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    minHeight: 140,
    justifyContent: 'center',
  },
  tileTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginTop: 8,
  },
  tileSubtitle: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  tileBadge: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#f44336',
    marginTop: 4,
  },
  statsContainer: {
    flexDirection: 'row',
    padding: 10,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    margin: 6,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginVertical: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  section: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  announcementCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  announcementHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  announcementTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginLeft: 8,
    flex: 1,
  },
  announcementMessage: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  announcementDate: {
    fontSize: 12,
    color: '#999',
  },
  motdContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    margin: 20,
    alignItems: 'center',
  },
  motdText: {
    flex: 1,
    fontSize: 14,
    fontStyle: 'italic',
    color: '#666',
    marginLeft: 12,
  },
});
