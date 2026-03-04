import { useState } from 'react';
import type { TimelineEvent } from '../lib/types';
import { getCategoryColor, getCategoryLabel, getDatePrecisionStyle, cn } from '../lib/utils';

interface TimelineEntryProps {
  event: TimelineEvent;
  isLast: boolean;
}

export function TimelineEntry({ event, isLast }: TimelineEntryProps) {
  const [expanded, setExpanded] = useState(false);
  const colors = getCategoryColor(event.category);
  const categoryLabel = getCategoryLabel(event.category);
  const datePrecisionStyle = getDatePrecisionStyle(event.date_precision);

  const displayDate = event.date_precision === 'unknown'
    ? 'Fecha desconocida'
    : event.date;

  return (
    <div className="relative flex gap-4">
      {/* Timeline line and dot */}
      <div className="flex flex-col items-center">
        <div className={cn('w-3.5 h-3.5 rounded-full border-2 border-white ring-2 ring-gray-200 flex-shrink-0 z-10', colors.dot)} />
        {!isLast && (
          <div className="w-0.5 bg-gray-200 flex-1 min-h-6" />
        )}
      </div>

      {/* Content card */}
      <div className={cn('flex-1 mb-6 rounded-lg border p-4', colors.bg, colors.border)}>
        {/* Header row */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex-1 min-w-0">
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-left w-full"
            >
              <h4 className="text-sm font-bold text-gray-900 leading-tight">
                {event.title}
              </h4>
            </button>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Category badge */}
            <span className={cn('text-xs font-medium px-2 py-0.5 rounded-full', colors.bg, colors.text, 'border', colors.border)}>
              {categoryLabel}
            </span>
          </div>
        </div>

        {/* Date */}
        <div className="flex items-center gap-2 mb-2">
          <span className={cn('text-xs px-2 py-0.5 rounded border bg-white', datePrecisionStyle)}>
            {displayDate}
          </span>
          {event.date_precision === 'approximate' && (
            <span className="text-xs text-gray-400 italic">aprox.</span>
          )}
        </div>

        {/* Description - always show first line, expand for full */}
        <p className={cn(
          'text-sm text-gray-700 leading-relaxed',
          !expanded && 'line-clamp-2'
        )}>
          {event.description}
        </p>

        {/* Expand/collapse */}
        {event.description.length > 150 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-primary-600 hover:text-primary-700 font-medium mt-1"
          >
            {expanded ? 'Ver menos' : 'Ver mas...'}
          </button>
        )}

        {/* Relevant details */}
        {expanded && event.relevant_details && event.relevant_details.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <p className="text-xs font-semibold text-gray-600 mb-1.5">Detalles:</p>
            <ul className="space-y-1">
              {event.relevant_details.map((detail, idx) => (
                <li key={idx} className="text-xs text-gray-600 flex items-start gap-1.5">
                  <span className="text-gray-400 mt-0.5">-</span>
                  <span>{detail}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Source document badge */}
        <div className="mt-2 flex items-center gap-1.5">
          <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span className="text-xs text-gray-400">{event.source_document}</span>
        </div>
      </div>
    </div>
  );
}
