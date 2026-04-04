import { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { MessageCircle } from 'lucide-react';
import { ResponseItem } from '../lib/api';
import ResponseClapButton from './ResponseClapButton';

interface CommentSectionProps {
  articleId: string;
}

export default function CommentSection({ articleId }: CommentSectionProps) {
  const { api, user } = useApp();
  const [comments, setComments] = useState<ResponseItem[]>([]);
  const [commentText, setCommentText] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Fetch responses for this article
  useEffect(() => {
    api
      .getResponses(articleId)
      .then((res) => setComments(res.data))
      .catch((err) => console.error('Failed to load responses:', err))
      .finally(() => setLoading(false));
  }, [api, articleId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim() || !user) return;

    setSubmitting(true);
    try {
      const newComment = await api.createResponse(articleId, user.id, commentText.trim());
      setComments((prev) => [newComment, ...prev]);
      setCommentText('');
    } catch (err) {
      console.error('Failed to post response:', err);
    }
    setSubmitting(false);
  };

  return (
    <div className="mt-12">
      <h3 className="text-2xl font-bold mb-6">Responses ({comments.length})</h3>

      {/* Comment Form */}
      {user ? (
        <form onSubmit={handleSubmit} className="mb-8">
          <div className="flex gap-3">
            {user.avatar && (
              <img src={user.avatar} alt={user.name} className="size-10 rounded-full" />
            )}
            <div className="flex-1">
              <textarea
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="What are your thoughts?"
                className="w-full p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black resize-none"
                rows={3}
              />
              <div className="flex justify-end mt-2">
                <button
                  type="submit"
                  disabled={!commentText.trim() || submitting}
                  className="px-4 py-2 bg-black text-white rounded-full hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {submitting ? 'Posting...' : 'Respond'}
                </button>
              </div>
            </div>
          </div>
        </form>
      ) : (
        <p className="text-gray-500 mb-8">Sign in to leave a response.</p>
      )}

      {/* Comments List */}
      <div className="space-y-6">
        {loading ? (
          <div className="space-y-6">
            {[1, 2].map((i) => (
              <div key={i} className="animate-pulse flex gap-3 pb-6 border-b border-gray-200">
                <div className="size-10 bg-gray-200 rounded-full" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-1/4" />
                  <div className="h-4 bg-gray-100 rounded w-3/4" />
                </div>
              </div>
            ))}
          </div>
        ) : comments.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <MessageCircle className="size-12 mx-auto mb-3 opacity-50" />
            <p>No responses yet. Be the first to share your thoughts!</p>
          </div>
        ) : (
          comments.map((comment) => (
            <div key={comment.id} className="flex gap-3 pb-6 border-b border-gray-200">
              {comment.author.avatar && (
                <img
                  src={comment.author.avatar}
                  alt={comment.author.name}
                  className="size-10 rounded-full"
                />
              )}
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-medium">{comment.author.name}</span>
                  <span className="text-sm text-gray-500">{comment.date}</span>
                </div>
                <p className="text-gray-800 mb-3">{comment.text}</p>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <ResponseClapButton
                    articleId={articleId}
                    responseId={comment.id}
                    initialClaps={comment.likes}
                  />
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
