import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../../utils/api';
import { useRouter } from 'expo-router';

export default function CoursesScreen() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [subjects, setSubjects] = useState([]);

  useEffect(() => {
    loadSubjects();
  }, []);

  const loadSubjects = async () => {
    try {
      const response = await api.get('/subjects');
      setSubjects(response.data);
    } catch (error) {
      console.error('Error loading subjects:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadSubjects();
  };

  const renderSubjectItem = ({ item }: any) => (
    <TouchableOpacity
      style={styles.subjectCard}
      onPress={() => router.push(`/subject/${item._id}`)}
    >
      <View style={styles.subjectHeader}>
        <View style={styles.subjectIcon}>
          <Ionicons name="book" size={24} color="#0066cc" />
        </View>
        <View style={styles.subjectInfo}>
          <Text style={styles.subjectCode}>{item.code}</Text>
          <Text style={styles.subjectName}>{item.name}</Text>
          <View style={styles.subjectMeta}>
            <Text style={styles.subjectMetaText}>{item.credits} Credits</Text>
            <Text style={styles.subjectMetaText}> • </Text>
            <Text style={styles.subjectMetaText}>{item.category}</Text>
          </View>
        </View>
        <Ionicons name="chevron-forward" size={24} color="#999" />
      </View>
      <View style={styles.subjectFooter}>
        <Text style={styles.hoursText}>
          L: {item.lecture_hours} | T: {item.tutorial_hours} | P: {item.practical_hours}
        </Text>
        <Text style={styles.evaluationText}>{item.evaluation_pattern}</Text>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0066cc" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>My Courses</Text>
      </View>
      <FlatList
        data={subjects}
        renderItem={renderSubjectItem}
        keyExtractor={(item: any) => item._id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="book-outline" size={64} color="#ccc" />
            <Text style={styles.emptyText}>No courses enrolled</Text>
          </View>
        }
      />
    </View>
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
  list: {
    padding: 16,
  },
  subjectCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  subjectHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  subjectIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#e3f2fd',
    justifyContent: 'center',
    alignItems: 'center',
  },
  subjectInfo: {
    flex: 1,
    marginLeft: 12,
  },
  subjectCode: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0066cc',
  },
  subjectName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginTop: 2,
  },
  subjectMeta: {
    flexDirection: 'row',
    marginTop: 4,
  },
  subjectMetaText: {
    fontSize: 12,
    color: '#999',
  },
  subjectFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  hoursText: {
    fontSize: 12,
    color: '#666',
  },
  evaluationText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '600',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
    marginTop: 16,
  },
});
