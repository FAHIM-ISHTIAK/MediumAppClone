import { InlineResponseItem } from '../lib/api';
import { X } from 'lucide-react';

interface InlineCommentViewerProps {
  comment: InlineResponseItem;
  onClose: () => void;
  position: { x: number; y: number };
}

export default function InlineCommentViewer({
  comment,
  onClose,
  position,
}: InlineCommentViewerProps) {
  return (
    <div
      className="fixed bg-white border border-gray-300 rounded-lg shadow-xl p-4 z-50 w-80"
      style={{
        left: `${position.x}px`,
        top: `${position.y + 20}px`,
        transform: 'translateX(-50%)',
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-xs text-gray-500">
            {new Date(comment.date).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
            })}
          </p>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
          <X className="size-4" />
        </button>
      </div>

      <p className="text-sm bg-yellow-50 border-l-2 border-yellow-400 pl-2 py-1 mb-3 italic text-gray-600">
        "{comment.selectedText}"
      </p>

      <p className="text-sm text-gray-800">{comment.text}</p>
    </div>
  );
}
