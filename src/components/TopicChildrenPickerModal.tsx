import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from './Icon';
import { supabase } from '../services/supabase';
import { getTopicLabel, sanitizeTopicLabel } from '../utils/topicNameUtils';

type TopicRow = {
  id: string;
  topic_name: string;
  display_name?: string | null;
  topic_level: number;
  parent_topic_id: string | null;
  sort_order?: number | null;
};

type Breadcrumb = { id: string; name: string };

type Props = {
  visible: boolean;
  userId: string;
  subjectId: string;
  subjectColor: string;
  startTopicId: string;
  startTopicName: string;
  discoveredTopicIds: Set<string>;
  onClose: () => void;
  onTopicAdded: (addedTopicId: string) => void;
};

export default function TopicChildrenPickerModal({
  visible,
  userId,
  subjectId,
  subjectColor,
  startTopicId,
  startTopicName,
  discoveredTopicIds,
  onClose,
  onTopicAdded,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [breadcrumbs, setBreadcrumbs] = useState<Breadcrumb[]>([]);
  const [topics, setTopics] = useState<TopicRow[]>([]);
  const [parentsWithChildren, setParentsWithChildren] = useState<Set<string>>(new Set());
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const currentParentId = breadcrumbs.length > 0 ? breadcrumbs[breadcrumbs.length - 1].id : startTopicId;
  const currentTitle = breadcrumbs.length > 0 ? breadcrumbs[breadcrumbs.length - 1].name : startTopicName;

  useEffect(() => {
    if (!visible) return;
    setBreadcrumbs([]);
    setSelectedIds(new Set());
  }, [visible, startTopicId]);

  useEffect(() => {
    if (!visible) return;
    void loadChildren(currentParentId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible, currentParentId]);

  const loadChildren = async (parentTopicId: string) => {
    try {
      setLoading(true);
      setSelectedIds(new Set());

      const { data, error } = await supabase
        .from('curriculum_topics')
        .select('id, topic_name, display_name, topic_level, parent_topic_id, sort_order')
        .eq('parent_topic_id', parentTopicId)
        .order('sort_order', { ascending: true })
        .order('topic_name', { ascending: true });

      if (error) throw error;
      const rows = (data || []) as TopicRow[];
      setTopics(rows);

      if (rows.length === 0) {
        setParentsWithChildren(new Set());
        return;
      }

      const ids = rows.map((r) => r.id);
      const { data: children, error: childError } = await supabase
        .from('curriculum_topics')
        .select('parent_topic_id')
        .in('parent_topic_id', ids);

      if (childError) {
        setParentsWithChildren(new Set());
        return;
      }
      const withKids = new Set<string>((children || []).map((c: any) => c.parent_topic_id).filter(Boolean));
      setParentsWithChildren(withKids);
    } catch (e) {
      console.error('[TopicChildrenPickerModal] loadChildren error', e);
      setTopics([]);
      setParentsWithChildren(new Set());
    } finally {
      setLoading(false);
    }
  };

  const visibleTopics = useMemo(() => {
    return topics.filter((t) => !discoveredTopicIds.has(t.id));
  }, [topics, discoveredTopicIds]);

  const toggleSelected = (topicId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(topicId)) next.delete(topicId);
      else next.add(topicId);
      return next;
    });
  };

  const selectAll = () => {
    setSelectedIds(new Set(visibleTopics.map((t) => t.id)));
  };

  const clearAll = () => {
    setSelectedIds(new Set());
  };

  const drillDown = (topic: TopicRow) => {
    const label = getTopicLabel(topic as any);
    setBreadcrumbs((prev) => [...prev, { id: topic.id, name: label }]);
  };

  const goBack = () => {
    setBreadcrumbs((prev) => prev.slice(0, -1));
  };

  const discoverViaRpcOrUpsert = async (topicId: string) => {
    const { error: rpcError } = await supabase.rpc('discover_topic', {
      p_user_id: userId,
      p_subject_id: subjectId,
      p_topic_id: topicId,
      p_discovery_method: 'tree',
      p_search_query: null,
    });

    if (!rpcError) return;

    const msg = String((rpcError as any)?.message || '');
    const looksLikeMissingFn =
      msg.includes('discover_topic') && (msg.includes('does not exist') || msg.includes('schema cache'));

    if (!looksLikeMissingFn) throw rpcError;

    const { error: upsertError } = await supabase.from('user_discovered_topics').upsert(
      {
        user_id: userId,
        subject_id: subjectId,
        topic_id: topicId,
        discovery_method: 'tree',
        is_newly_discovered: true,
      } as any,
      { onConflict: 'user_id,topic_id' }
    );

    if (upsertError) throw upsertError;
  };

  const handleAddSelected = async () => {
    if (selectedIds.size === 0) return;
    try {
      setSaving(true);
      const ids = Array.from(selectedIds);
      for (const id of ids) {
        await discoverViaRpcOrUpsert(id);
      }
      onTopicAdded(ids[0]);
      onClose();
    } catch (e) {
      console.error('[TopicChildrenPickerModal] addSelected error', e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      <View style={styles.container}>
        <View style={[styles.header, { borderBottomColor: subjectColor + '33' }]}>
          <View style={styles.headerRow}>
            <TouchableOpacity onPress={breadcrumbs.length > 0 ? goBack : onClose} style={styles.headerIconBtn}>
              <Icon name={breadcrumbs.length > 0 ? 'arrow-back' : 'close'} size={24} color={subjectColor} />
            </TouchableOpacity>
            <View style={{ flex: 1 }}>
              <Text style={styles.headerTitle}>Add to Tree</Text>
              <Text style={styles.headerSubtitle} numberOfLines={1}>
                {sanitizeTopicLabel(currentTitle)}
              </Text>
            </View>
          </View>

          <View style={styles.headerActionsRow}>
            <TouchableOpacity onPress={selectAll} style={styles.smallBtn}>
              <Text style={[styles.smallBtnText, { color: subjectColor }]}>Select all</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={clearAll} style={styles.smallBtn}>
              <Text style={styles.smallBtnText}>Clear</Text>
            </TouchableOpacity>
          </View>
        </View>

        {loading ? (
          <View style={styles.loading}>
            <ActivityIndicator size="large" color={subjectColor} />
            <Text style={styles.loadingText}>Loading topics…</Text>
          </View>
        ) : (
          <ScrollView style={styles.list}>
            {visibleTopics.length === 0 ? (
              <View style={styles.empty}>
                <Icon name="checkmark-circle" size={44} color="#94A3B8" />
                <Text style={styles.emptyTitle}>All set</Text>
                <Text style={styles.emptyText}>No new topics to add at this level.</Text>
              </View>
            ) : (
              visibleTopics.map((t) => {
                const label = getTopicLabel(t as any);
                const checked = selectedIds.has(t.id);
                const hasChildren = parentsWithChildren.has(t.id);

                return (
                  <TouchableOpacity
                    key={t.id}
                    style={[styles.row, checked && styles.rowSelected]}
                    onPress={() => toggleSelected(t.id)}
                    onLongPress={() => (hasChildren ? drillDown(t) : undefined)}
                    delayLongPress={300}
                  >
                    <View style={styles.rowLeft}>
                      <Text style={[styles.checkbox, { color: checked ? subjectColor : '#64748B' }]}>
                        {checked ? '☑' : '☐'}
                      </Text>
                      <View style={{ flex: 1, marginLeft: 12 }}>
                        <Text style={styles.rowTitle} numberOfLines={2}>
                          {sanitizeTopicLabel(label)}
                        </Text>
                        <Text style={styles.rowMeta}>Level {t.topic_level}</Text>
                      </View>
                    </View>

                    {hasChildren ? (
                      <TouchableOpacity
                        onPress={() => drillDown(t)}
                        style={styles.chevronBtn}
                        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                      >
                        <Icon name="chevron-forward" size={20} color="#94A3B8" />
                      </TouchableOpacity>
                    ) : null}
                  </TouchableOpacity>
                );
              })
            )}
            <View style={{ height: 24 }} />
          </ScrollView>
        )}

        <View style={styles.footer}>
          <TouchableOpacity
            style={[
              styles.addBtn,
              { backgroundColor: subjectColor },
              (saving || selectedIds.size === 0) && styles.addBtnDisabled,
            ]}
            onPress={handleAddSelected}
            disabled={saving || selectedIds.size === 0}
          >
            {saving ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.addBtnText}>
                Add {selectedIds.size > 0 ? selectedIds.size : ''} topic{selectedIds.size === 1 ? '' : 's'}
              </Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0B0B0F' },
  header: { paddingTop: 18, paddingHorizontal: 16, paddingBottom: 12, borderBottomWidth: 1 },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerIconBtn: { padding: 8 },
  headerTitle: { color: '#fff', fontSize: 16, fontWeight: '800' },
  headerSubtitle: { color: '#94A3B8', fontSize: 12, marginTop: 2 },
  headerActionsRow: { flexDirection: 'row', gap: 12, marginTop: 10 },
  smallBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: 'rgba(255,255,255,0.06)',
  },
  smallBtnText: { color: '#CBD5E1', fontSize: 12, fontWeight: '700' },
  loading: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10 },
  loadingText: { color: '#94A3B8' },
  list: { flex: 1, paddingHorizontal: 16, paddingTop: 12 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
    borderRadius: 14,
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
    marginBottom: 10,
  },
  rowSelected: { borderColor: 'rgba(0,245,255,0.35)', backgroundColor: 'rgba(0,245,255,0.06)' },
  rowLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  checkbox: { fontSize: 18, fontWeight: '900' },
  rowTitle: { color: '#fff', fontSize: 14, fontWeight: '700' },
  rowMeta: { color: '#64748B', fontSize: 12, marginTop: 4 },
  chevronBtn: { padding: 6, marginLeft: 10 },
  empty: { padding: 28, alignItems: 'center', gap: 10 },
  emptyTitle: { color: '#fff', fontSize: 16, fontWeight: '800' },
  emptyText: { color: '#94A3B8', textAlign: 'center' },
  footer: { padding: 16, borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.06)' },
  addBtn: { paddingVertical: 14, borderRadius: 14, alignItems: 'center' },
  addBtnDisabled: { opacity: 0.5 },
  addBtnText: { color: '#000', fontWeight: '900' },
});

import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from './Icon';
import { supabase } from '../services/supabase';
import { getTopicLabel, sanitizeTopicLabel } from '../utils/topicNameUtils';

type TopicRow = {
  id: string;
  topic_name: string;
  display_name?: string | null;
  topic_level: number;
  parent_topic_id: string | null;
  sort_order?: number | null;
};

type Breadcrumb = { id: string; name: string };

type Props = {
  visible: boolean;
  userId: string;
  subjectId: string;
  subjectColor: string;
  startTopicId: string;
  startTopicName: string;
  discoveredTopicIds: Set<string>;
  onClose: () => void;
  onTopicAdded: (addedTopicId: string) => void;
};

export default function TopicChildrenPickerModal({
  visible,
  userId,
  subjectId,
  subjectColor,
  startTopicId,
  startTopicName,
  discoveredTopicIds,
  onClose,
  onTopicAdded,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [breadcrumbs, setBreadcrumbs] = useState<Breadcrumb[]>([]);
  const [topics, setTopics] = useState<TopicRow[]>([]);
  const [parentsWithChildren, setParentsWithChildren] = useState<Set<string>>(new Set());
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const currentParentId = breadcrumbs.length > 0 ? breadcrumbs[breadcrumbs.length - 1].id : startTopicId;
  const currentTitle = breadcrumbs.length > 0 ? breadcrumbs[breadcrumbs.length - 1].name : startTopicName;

  useEffect(() => {
    if (!visible) return;
    // Reset to initial state when opened.
    setBreadcrumbs([]);
    setSelectedIds(new Set());
  }, [visible, startTopicId]);

  useEffect(() => {
    if (!visible) return;
    void loadChildren(currentParentId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible, currentParentId]);

  const loadChildren = async (parentTopicId: string) => {
    try {
      setLoading(true);
      setSelectedIds(new Set());

      const { data, error } = await supabase
        .from('curriculum_topics')
        .select('id, topic_name, display_name, topic_level, parent_topic_id, sort_order')
        .eq('parent_topic_id', parentTopicId)
        .order('sort_order', { ascending: true })
        .order('topic_name', { ascending: true });

      if (error) throw error;
      const rows = (data || []) as TopicRow[];
      setTopics(rows);

      // Determine which of these rows have children (so we can show a drill-down chevron).
      if (rows.length === 0) {
        setParentsWithChildren(new Set());
        return;
      }

      const ids = rows.map((r) => r.id);
      const { data: children, error: childError } = await supabase
        .from('curriculum_topics')
        .select('parent_topic_id')
        .in('parent_topic_id', ids);

      if (childError) {
        // Non-fatal: just hide drill-down affordance.
        setParentsWithChildren(new Set());
        return;
      }
      const withKids = new Set<string>((children || []).map((c: any) => c.parent_topic_id).filter(Boolean));
      setParentsWithChildren(withKids);
    } catch (e) {
      console.error('[TopicChildrenPickerModal] loadChildren error', e);
      setTopics([]);
      setParentsWithChildren(new Set());
    } finally {
      setLoading(false);
    }
  };

  const visibleTopics = useMemo(() => {
    // Hide already-discovered topics (they’re already in the tree).
    return topics.filter((t) => !discoveredTopicIds.has(t.id));
  }, [topics, discoveredTopicIds]);

  const toggleSelected = (topicId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(topicId)) next.delete(topicId);
      else next.add(topicId);
      return next;
    });
  };

  const selectAll = () => {
    setSelectedIds(new Set(visibleTopics.map((t) => t.id)));
  };

  const clearAll = () => {
    setSelectedIds(new Set());
  };

  const drillDown = (topic: TopicRow) => {
    const label = getTopicLabel(topic as any);
    setBreadcrumbs((prev) => [...prev, { id: topic.id, name: label }]);
  };

  const goBack = () => {
    setBreadcrumbs((prev) => prev.slice(0, -1));
  };

  const discoverViaRpcOrUpsert = async (topicId: string) => {
    // Prefer RPC if present (updates completion %). Fall back to upsert if RPC isn’t deployed.
    const { error: rpcError } = await supabase.rpc('discover_topic', {
      p_user_id: userId,
      p_subject_id: subjectId,
      p_topic_id: topicId,
      p_discovery_method: 'tree',
      p_search_query: null,
    });

    if (!rpcError) return;

    const msg = String((rpcError as any)?.message || '');
    const looksLikeMissingFn =
      msg.includes('discover_topic') && (msg.includes('does not exist') || msg.includes('schema cache'));

    if (!looksLikeMissingFn) {
      throw rpcError;
    }

    const { error: upsertError } = await supabase.from('user_discovered_topics').upsert(
      {
        user_id: userId,
        subject_id: subjectId,
        topic_id: topicId,
        discovery_method: 'tree',
        is_newly_discovered: true,
      } as any,
      { onConflict: 'user_id,topic_id' }
    );

    if (upsertError) throw upsertError;
  };

  const handleAddSelected = async () => {
    if (selectedIds.size === 0) return;
    try {
      setSaving(true);
      const ids = Array.from(selectedIds);
      for (const id of ids) {
        await discoverViaRpcOrUpsert(id);
      }
      // Inform parent and close.
      onTopicAdded(ids[0]);
      onClose();
    } catch (e) {
      console.error('[TopicChildrenPickerModal] addSelected error', e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      <View style={styles.container}>
        <View style={[styles.header, { borderBottomColor: subjectColor + '33' }]}>
          <View style={styles.headerRow}>
            <TouchableOpacity onPress={breadcrumbs.length > 0 ? goBack : onClose} style={styles.headerIconBtn}>
              <Icon name={breadcrumbs.length > 0 ? 'arrow-back' : 'close'} size={24} color={subjectColor} />
            </TouchableOpacity>
            <View style={{ flex: 1 }}>
              <Text style={styles.headerTitle}>Add to Tree</Text>
              <Text style={styles.headerSubtitle} numberOfLines={1}>
                {sanitizeTopicLabel(currentTitle)}
              </Text>
            </View>
          </View>

          <View style={styles.headerActionsRow}>
            <TouchableOpacity onPress={selectAll} style={styles.smallBtn}>
              <Text style={[styles.smallBtnText, { color: subjectColor }]}>Select all</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={clearAll} style={styles.smallBtn}>
              <Text style={styles.smallBtnText}>Clear</Text>
            </TouchableOpacity>
          </View>
        </View>

        {loading ? (
          <View style={styles.loading}>
            <ActivityIndicator size="large" color={subjectColor} />
            <Text style={styles.loadingText}>Loading topics…</Text>
          </View>
        ) : (
          <ScrollView style={styles.list}>
            {visibleTopics.length === 0 ? (
              <View style={styles.empty}>
                <Icon name="checkmark-circle-outline" size={44} color="#94A3B8" />
                <Text style={styles.emptyTitle}>All set</Text>
                <Text style={styles.emptyText}>No new topics to add at this level.</Text>
              </View>
            ) : (
              visibleTopics.map((t) => {
                const label = getTopicLabel(t as any);
                const checked = selectedIds.has(t.id);
                const hasChildren = parentsWithChildren.has(t.id);

                return (
                  <TouchableOpacity
                    key={t.id}
                    style={[styles.row, checked && styles.rowSelected]}
                    onPress={() => toggleSelected(t.id)}
                    onLongPress={() => (hasChildren ? drillDown(t) : undefined)}
                    delayLongPress={300}
                  >
                    <View style={styles.rowLeft}>
                      <Icon
                        name={checked ? 'checkbox' : 'square-outline'}
                        size={22}
                        color={checked ? subjectColor : '#64748B'}
                      />
                      <View style={{ flex: 1, marginLeft: 12 }}>
                        <Text style={styles.rowTitle} numberOfLines={2}>
                          {sanitizeTopicLabel(label)}
                        </Text>
                        <Text style={styles.rowMeta}>Level {t.topic_level}</Text>
                      </View>
                    </View>

                    {hasChildren ? (
                      <TouchableOpacity
                        onPress={() => drillDown(t)}
                        style={styles.chevronBtn}
                        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                      >
                        <Icon name="chevron-forward" size={20} color="#94A3B8" />
                      </TouchableOpacity>
                    ) : null}
                  </TouchableOpacity>
                );
              })
            )}
            <View style={{ height: 24 }} />
          </ScrollView>
        )}

        <View style={styles.footer}>
          <TouchableOpacity
            style={[styles.addBtn, { backgroundColor: subjectColor }, (saving || selectedIds.size === 0) && styles.addBtnDisabled]}
            onPress={handleAddSelected}
            disabled={saving || selectedIds.size === 0}
          >
            {saving ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.addBtnText}>
                Add {selectedIds.size > 0 ? selectedIds.size : ''} topic{selectedIds.size === 1 ? '' : 's'}
              </Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0B0B0F' },
  header: { paddingTop: 18, paddingHorizontal: 16, paddingBottom: 12, borderBottomWidth: 1 },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerIconBtn: { padding: 8 },
  headerTitle: { color: '#fff', fontSize: 16, fontWeight: '800' },
  headerSubtitle: { color: '#94A3B8', fontSize: 12, marginTop: 2 },
  headerActionsRow: { flexDirection: 'row', gap: 12, marginTop: 10 },
  smallBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: 'rgba(255,255,255,0.06)',
  },
  smallBtnText: { color: '#CBD5E1', fontSize: 12, fontWeight: '700' },
  loading: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10 },
  loadingText: { color: '#94A3B8' },
  list: { flex: 1, paddingHorizontal: 16, paddingTop: 12 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
    borderRadius: 14,
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
    marginBottom: 10,
  },
  rowSelected: { borderColor: 'rgba(0,245,255,0.35)', backgroundColor: 'rgba(0,245,255,0.06)' },
  rowLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  rowTitle: { color: '#fff', fontSize: 14, fontWeight: '700' },
  rowMeta: { color: '#64748B', fontSize: 12, marginTop: 4 },
  chevronBtn: { padding: 6, marginLeft: 10 },
  empty: { padding: 28, alignItems: 'center', gap: 10 },
  emptyTitle: { color: '#fff', fontSize: 16, fontWeight: '800' },
  emptyText: { color: '#94A3B8', textAlign: 'center' },
  footer: { padding: 16, borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.06)' },
  addBtn: { paddingVertical: 14, borderRadius: 14, alignItems: 'center' },
  addBtnDisabled: { opacity: 0.5 },
  addBtnText: { color: '#000', fontWeight: '900' },
});

