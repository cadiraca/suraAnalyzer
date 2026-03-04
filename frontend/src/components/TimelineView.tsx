import type { TimelineEvent } from '../lib/types';
import { TimelineEntry } from './TimelineEntry';

interface TimelineViewProps {
  events: TimelineEvent[];
}

export function TimelineView({ events }: TimelineViewProps) {
  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p className="text-sm">No se encontraron eventos clinicos en los documentos.</p>
      </div>
    );
  }

  return (
    <div className="py-2">
      {events.map((event, index) => (
        <TimelineEntry
          key={`${event.date}-${event.title}-${index}`}
          event={event}
          isLast={index === events.length - 1}
        />
      ))}
    </div>
  );
}
