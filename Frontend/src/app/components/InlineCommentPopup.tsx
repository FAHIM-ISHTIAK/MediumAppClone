import { useState } from 'react';
import { useApp } from '../context/AppContext';
import { X } from 'lucide-react';
import { InlineResponseItem } from '../lib/api';

interface InlineCommentPopupProps {
  articleId: string;
  selectedText: string;
  position: { x: number; y: number };
  onClose: () => void;
  onCreated?: (comment: InlineResponseItem) => void;
}

export default function InlineCommentPopup({
  articleId,
  selectedText,
  position,
  onClose,
  onCreated,
}: InlineCommentPopupProps) {
  const { api, user } = useApp();
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!comment.trim() || !user) return;

    setSubmitting(true);
    try {
      const result = await api.createInlineResponse(articleId, user.id, {
        selectedText,
        paragraphIndex: 0, // simplified — could be computed from DOM position
        text: comment.trim(),
      });
      onCreated?.(result);
      onClose();
    } catch (err) {
      console.error('Failed to create inline comment:', err);
    }
    setSubmitting(false);
  };

  if (!user) return null;

  return (
    <div
      className="fixed bg-white border border-gray-300 rounded-lg shadow-xl p-4 z-50 w-96"
      style={{
        left: `${position.x}px`,
        top: `${position.y + 20}px`,
        transform: 'translateX(-50%)',
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className="text-sm text-gray-600 mb-2">Commenting on:</p>
          <p className="text-sm bg-yellow-50 border-l-2 border-yellow-400 pl-2 py-1 italic">
            "{selectedText}"
          </p>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
          <X className="size-4" />
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Write your comment..."
          className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-black resize-none"
          rows={3}
          autoFocus
        />
        <div className="flex justify-end gap-2 mt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!comment.trim() || submitting}
            className="px-3 py-1.5 text-sm bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-300"
          >
            {submitting ? 'Posting...' : 'Comment'}
          </button>
        </div>
      </form>
    </div>
  );
}
