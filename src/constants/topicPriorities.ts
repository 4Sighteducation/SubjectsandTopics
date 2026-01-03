export interface TopicPriorityLevel {
  value: number;
  number: string;
  label: string;
  color: string;
  description: string;
}

// NOTE: 1 = highest priority (most urgent).
export const TOPIC_PRIORITY_LEVELS: TopicPriorityLevel[] = [
  {
    value: 1,
    number: '1',
    label: '🔥 Urgent',
    color: '#EF4444',
    description: 'Top priority. Critical for exams.',
  },
  {
    value: 2,
    number: '2',
    label: '⚡ High Priority',
    color: '#FF006E',
    description: 'Important topic. Needs focus soon.',
  },
  {
    value: 3,
    number: '3',
    label: '📌 Medium Priority',
    color: '#F59E0B',
    description: 'Useful to know. Review when ready.',
  },
  {
    value: 4,
    number: '4',
    label: '✅ Low Priority',
    color: '#10B981',
    description: 'Good to know. Review occasionally.',
  },
];

export function getTopicPriorityInfo(priority: number | null | undefined): TopicPriorityLevel | null {
  if (!priority) return null;
  return TOPIC_PRIORITY_LEVELS.find((p) => p.value === priority) || null;
}

export interface TopicPriorityLevel {
  value: number;
  number: string;
  label: string;
  color: string;
  description: string;
}

// NOTE: 1 = highest priority (most urgent).
export const TOPIC_PRIORITY_LEVELS: TopicPriorityLevel[] = [
  {
    value: 1,
    number: '1',
    label: '🔥 Urgent',
    color: '#EF4444',
    description: 'Top priority. Critical for exams.',
  },
  {
    value: 2,
    number: '2',
    label: '⚡ High Priority',
    color: '#FF006E',
    description: 'Important topic. Needs focus soon.',
  },
  {
    value: 3,
    number: '3',
    label: '📌 Medium Priority',
    color: '#F59E0B',
    description: 'Useful to know. Review when ready.',
  },
  {
    value: 4,
    number: '4',
    label: '✅ Low Priority',
    color: '#10B981',
    description: 'Good to know. Review occasionally.',
  },
];

export function getTopicPriorityInfo(priority: number | null | undefined): TopicPriorityLevel | null {
  if (!priority) return null;
  return TOPIC_PRIORITY_LEVELS.find((p) => p.value === priority) || null;
}

