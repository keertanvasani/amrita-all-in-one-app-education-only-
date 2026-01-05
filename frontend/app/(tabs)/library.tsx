import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../../utils/api';
import { format } from 'date-fns';

export default function LibraryScreen() {
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [books, setBooks] = useState([]);
  const [issuedBooks, setIssuedBooks] = useState([]);
  const [activeTab, setActiveTab] = useState('search'); // search or issued

  useEffect(() => {
    if (activeTab === 'issued') {
      loadIssuedBooks();
    }
  }, [activeTab]);

  const searchBooks = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await api.get('/library/books', {
        params: { query: searchQuery },
      });
      setBooks(response.data);
    } catch (error) {
      console.error('Error searching books:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadIssuedBooks = async () => {
    setLoading(true);
    try {
      const response = await api.get('/library/issued');
      setIssuedBooks(response.data);
    } catch (error) {
      console.error('Error loading issued books:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderBookItem = ({ item }: any) => (
    <View style={styles.bookCard}>
      <View style={styles.bookIcon}>
        <Ionicons name="book" size={32} color="#0066cc" />
      </View>
      <View style={styles.bookInfo}>
        <Text style={styles.bookTitle}>{item.title}</Text>
        <Text style={styles.bookAuthor}>{item.author}</Text>
        <Text style={styles.bookMeta}>
          ISBN: {item.isbn} • {item.category}
        </Text>
        <View style={styles.availabilityRow}>
          <Ionicons
            name={item.available_copies > 0 ? 'checkmark-circle' : 'close-circle'}
            size={16}
            color={item.available_copies > 0 ? '#4caf50' : '#f44336'}
          />
          <Text style={[styles.availability, {
            color: item.available_copies > 0 ? '#4caf50' : '#f44336'
          }]}>
            {item.available_copies}/{item.total_copies} Available
          </Text>
        </View>
      </View>
    </View>
  );

  const renderIssuedItem = ({ item }: any) => (
    <View style={styles.issuedCard}>
      <View style={styles.issuedHeader}>
        <Text style={styles.bookTitle}>{item.book?.title}</Text>
        <View style={[styles.statusBadge, {
          backgroundColor: item.status === 'issued' ? '#e3f2fd' : '#ffebee'
        }]}>
          <Text style={[styles.statusText, {
            color: item.status === 'issued' ? '#0066cc' : '#f44336'
          }]}>
            {item.status === 'issued' ? 'Issued' : 'Overdue'}
          </Text>
        </View>
      </View>
      <Text style={styles.bookAuthor}>{item.book?.author}</Text>
      <View style={styles.datesContainer}>
        <View style={styles.dateItem}>
          <Text style={styles.dateLabel}>Issued:</Text>
          <Text style={styles.dateValue}>
            {format(new Date(item.issue_date), 'MMM d, yyyy')}
          </Text>
        </View>
        <View style={styles.dateItem}>
          <Text style={styles.dateLabel}>Due:</Text>
          <Text style={[styles.dateValue, item.status === 'overdue' && styles.overdueText]}>
            {format(new Date(item.due_date), 'MMM d, yyyy')}
          </Text>
        </View>
      </View>
      {item.fine_amount > 0 && (
        <Text style={styles.fineText}>Fine: ₹{item.fine_amount}</Text>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Library</Text>
      </View>

      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'search' && styles.activeTab]}
          onPress={() => setActiveTab('search')}
        >
          <Text style={[styles.tabText, activeTab === 'search' && styles.activeTabText]}>
            Search Books
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'issued' && styles.activeTab]}
          onPress={() => setActiveTab('issued')}
        >
          <Text style={[styles.tabText, activeTab === 'issued' && styles.activeTabText]}>
            Issued Books
          </Text>
        </TouchableOpacity>
      </View>

      {activeTab === 'search' ? (
        <View style={styles.content}>
          <View style={styles.searchContainer}>
            <TextInput
              style={styles.searchInput}
              placeholder="Search by title, author, or ISBN"
              value={searchQuery}
              onChangeText={setSearchQuery}
              onSubmitEditing={searchBooks}
            />
            <TouchableOpacity style={styles.searchButton} onPress={searchBooks}>
              <Ionicons name="search" size={24} color="#fff" />
            </TouchableOpacity>
          </View>

          {loading ? (
            <ActivityIndicator size="large" color="#0066cc" style={{ marginTop: 20 }} />
          ) : (
            <FlatList
              data={books}
              renderItem={renderBookItem}
              keyExtractor={(item: any) => item._id}
              contentContainerStyle={styles.list}
              ListEmptyComponent={
                <View style={styles.emptyContainer}>
                  <Ionicons name="search" size={64} color="#ccc" />
                  <Text style={styles.emptyText}>
                    {searchQuery ? 'No books found' : 'Enter search query to find books'}
                  </Text>
                </View>
              }
            />
          )}
        </View>
      ) : (
        loading ? (
          <ActivityIndicator size="large" color="#0066cc" style={{ marginTop: 20 }} />
        ) : (
          <FlatList
            data={issuedBooks}
            renderItem={renderIssuedItem}
            keyExtractor={(item: any) => item._id}
            contentContainerStyle={styles.list}
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Ionicons name="book-outline" size={64} color="#ccc" />
                <Text style={styles.emptyText}>No books issued</Text>
              </View>
            }
          />
        )
      )}
    </View>
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
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#0066cc',
  },
  tabText: {
    fontSize: 14,
    color: '#999',
    fontWeight: '600',
  },
  activeTabText: {
    color: '#0066cc',
  },
  content: {
    flex: 1,
  },
  searchContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
  },
  searchInput: {
    flex: 1,
    height: 48,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    paddingHorizontal: 16,
    fontSize: 16,
  },
  searchButton: {
    width: 48,
    height: 48,
    backgroundColor: '#0066cc',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  list: {
    padding: 16,
  },
  bookCard: {
    flexDirection: 'row',
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
  bookIcon: {
    width: 56,
    height: 56,
    borderRadius: 8,
    backgroundColor: '#e3f2fd',
    justifyContent: 'center',
    alignItems: 'center',
  },
  bookInfo: {
    flex: 1,
    marginLeft: 12,
  },
  bookTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  bookAuthor: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  bookMeta: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  availabilityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  availability: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  issuedCard: {
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
  issuedHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  datesContainer: {
    flexDirection: 'row',
    marginTop: 12,
  },
  dateItem: {
    flex: 1,
  },
  dateLabel: {
    fontSize: 12,
    color: '#999',
  },
  dateValue: {
    fontSize: 14,
    color: '#333',
    fontWeight: '600',
    marginTop: 4,
  },
  overdueText: {
    color: '#f44336',
  },
  fineText: {
    fontSize: 14,
    color: '#f44336',
    fontWeight: '600',
    marginTop: 12,
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
    textAlign: 'center',
  },
});
