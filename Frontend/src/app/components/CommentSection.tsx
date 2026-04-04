import { useState, useEffect, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { MessageCircle, Reply, ChevronDown, ChevronUp, MoreVertical } from 'lucide-react';
import { ResponseItem } from '../lib/api';
import ResponseClapButton from './ResponseClapButton';

interface CommentSectionProps {
  articleId: string;
}

/* ── Single comment thread (recursive) ─────────────────────────────── */

interface CommentThreadProps {
  comment: ResponseItem;
  articleId: string;
  depth: number;
  onDeleted: (id: string, countRemoved: number) => void;
  onUpdated?: (id: string, updatedComment: ResponseItem) => void;
}

function CommentThread({
  comment,
  articleId,
  depth,
  onDeleted,
  onUpdated,
}: CommentThreadProps) {
  const { api, user } = useApp();
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [replies, setReplies] = useState<ResponseItem[]>([]);
  const [repliesLoaded, setRepliesLoaded] = useState(false);
  const [showReplies, setShowReplies] = useState(false);
  const [replyCount, setReplyCount] = useState(comment.replyCount);
  const [deleting, setDeleting] = useState(false);
  const [replyPage, setReplyPage] = useState(1);
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(comment.text);
  const [editSubmitting, setEditSubmitting] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [currentComment, setCurrentComment] = useState(comment);
  const menuRef = useRef<HTMLDivElement>(null);
  const REPLIES_PER_PAGE = 3;

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadReplies = async () => {
    try {
      const res = await api.getReplies(articleId, comment.id, 1, 100);
      setReplies(res.data);
      setRepliesLoaded(true);
      setReplyPage(1);
    } catch (err) {
      console.error('Failed to load replies:', err);
    }
  };

  const toggleReplies = async () => {
    if (!repliesLoaded) {
      await loadReplies();
    }
    setShowReplies((prev) => !prev);
  };

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim() || !user) return;
    setSubmitting(true);
    try {
      const newReply = await api.createReply(articleId, comment.id, user.id, replyText.trim());
      setReplies((prev) => [...prev, newReply]);
      setReplyCount((c) => c + 1);
      setReplyText('');
      setShowReplyForm(false);
      setShowReplies(true);
      setRepliesLoaded(true);
    } catch (err) {
      console.error('Failed to post reply:', err);
    }
    setSubmitting(false);
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editText.trim() || !user) return;
    setEditSubmitting(true);
    try {
      const updated = await api.updateResponse(
        articleId,
        user.id,
        comment.id,
        editText.trim()
      );
      setCurrentComment(updated);
      setIsEditing(false);
      setShowMenu(false);
      onUpdated?.(comment.id, updated);
    } catch (err) {
      console.error('Failed to edit response:', err);
    }
    setEditSubmitting(false);
  };

  const handleDelete = async () => {
    if (!user) return;
    setDeleting(true);
    try {
      await api.deleteResponse(articleId, user.id, comment.id);
      onDeleted(comment.id, 1 + replyCount);
    } catch (err) {
      console.error('Failed to delete response:', err);
      setDeleting(false);
    }
  };

  const handleChildDeleted = (childId: string, countRemoved: number) => {
    setReplies((prev) => prev.filter((r) => r.id !== childId));
    setReplyCount((c) => Math.max(c - countRemoved, 0));
  };

  const handleChildUpdated = (childId: string, updated: ResponseItem) => {
    setReplies((prev) =>
      prev.map((r) => (r.id === childId ? updated : r))
    );
  };

  return (
    <div className={`flex gap-3 ${depth === 0 ? 'pb-6 border-b border-gray-200' : 'pt-4'}`}>
      {currentComment.author.avatar && (
        <img
          src={currentComment.author.avatar}
          alt={currentComment.author.name}
          className="size-8 rounded-full flex-shrink-0"
        />
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-sm">{currentComment.author.name}</span>
          <span className="text-xs text-gray-500">{currentComment.date}</span>
          {currentComment.isEdited && <span className="text-sm font-semibold text-gray-700">(edited)</span>}
        </div>

        {isEditing ? (
          <form onSubmit={handleEdit} className="mb-2">
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black resize-none text-sm"
              rows={2}
            />
            <div className="flex justify-end gap-2 mt-2">
              <button
                type="button"
                onClick={() => {
                  setIsEditing(false);
                  setEditText(currentComment.text);
                }}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!editText.trim() || editSubmitting}
                className="px-3 py-1 text-sm bg-black text-white rounded-full hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {editSubmitting ? 'Saving...' : 'Save'}
              </button>
            </div>
          </form>
        ) : (
          <p className="text-gray-800 mb-2 text-sm">{currentComment.text}</p>
        )}

        {/* Action buttons */}
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <ResponseClapButton
            articleId={articleId}
            responseId={currentComment.id}
            initialClaps={currentComment.likes}
          />

          {user && (
            <button
              onClick={() => setShowReplyForm((prev) => !prev)}
              className="flex items-center gap-1 hover:text-gray-800 transition-colors"
            >
              <Reply className="size-4" />
              Reply
            </button>
          )}

          {replyCount > 0 && (
            <button
              onClick={toggleReplies}
              className="flex items-center gap-1 hover:text-gray-800 transition-colors font-medium"
            >
              {showReplies ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
              {replyCount} {replyCount === 1 ? 'reply' : 'replies'}
            </button>
          )}

          {/* 3-dot menu */}
          {user && user.id === currentComment.author.id && (
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setShowMenu((prev) => !prev)}
                className="hover:text-gray-800 transition-colors"
              >
                <MoreVertical className="size-4" />
              </button>
              {showMenu && (
                <div className="absolute right-0 mt-1 w-32 bg-white border border-gray-300 rounded-lg shadow-lg z-10">
                  <button
                    onClick={() => {
                      setIsEditing(true);
                      setShowMenu(false);
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Edit
                  </button>
                  <button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100 disabled:opacity-50"
                  >
                    {deleting ? 'Deleting...' : 'Delete'}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Reply form */}
        {showReplyForm && user && (
          <form onSubmit={handleReply} className="mt-3">
            <textarea
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder={`Reply to ${currentComment.author.name}...`}
              className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black resize-none text-sm"
              rows={2}
            />
            <div className="flex justify-end gap-2 mt-2">
              <button
                type="button"
                onClick={() => {
                  setShowReplyForm(false);
                  setReplyText('');
                }}
                className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!replyText.trim() || submitting}
                className="px-3 py-1.5 text-sm bg-black text-white rounded-full hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {submitting ? 'Posting...' : 'Reply'}
              </button>
            </div>
          </form>
        )}

        {/* Nested replies */}
        {showReplies && replies.length > 0 && (
          <div className="ml-2 border-l-2 border-gray-100 pl-3 mt-2">
            {replies.slice(0, replyPage * REPLIES_PER_PAGE).map((reply) => (
              <CommentThread
                key={reply.id}
                comment={reply}
                articleId={articleId}
                depth={depth + 1}
                onDeleted={handleChildDeleted}
                onUpdated={handleChildUpdated}
              />
            ))}
            {replies.length > replyPage * REPLIES_PER_PAGE && (
              <button
                onClick={() => setReplyPage((p) => p + 1)}
                className="mt-2 text-sm text-gray-600 hover:text-gray-800 font-medium"
              >
                See more replies
              </button>
            )}
            {replyPage > 1 && (
              <button
                onClick={() => setReplyPage(1)}
                className="mt-2 ml-2 text-sm text-gray-600 hover:text-gray-800 font-medium"
              >
                See less
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Main comment section ──────────────────────────────────────────── */

export default function CommentSection({ articleId }: CommentSectionProps) {
  const { api, user } = useApp();
  const [comments, setComments] = useState<ResponseItem[]>([]);
  const [commentText, setCommentText] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [totalResponseCount, setTotalResponseCount] = useState(0);

  // Fetch top-level responses for this article
  useEffect(() => {
    api
      .getResponses(articleId)
      .then((res) => {
        setComments(res.data);
        setTotalResponseCount(res.totalResponseCount ?? res.total_response_count ?? 0);
      })
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
      setTotalResponseCount((c) => c + 1);
    } catch (err) {
      console.error('Failed to post response:', err);
    }
    setSubmitting(false);
  };

  const handleTopLevelDeleted = (id: string, countRemoved: number) => {
    setComments((prev) => prev.filter((c) => c.id !== id));
    setTotalResponseCount((c) => Math.max(c - countRemoved, 0));
  };

  const handleTopLevelUpdated = (id: string, updated: ResponseItem) => {
    setComments((prev) =>
      prev.map((c) => (c.id === id ? updated : c))
    );
  };

  return (
    <div className="mt-12">
      <h3 className="text-2xl font-bold mb-6">Responses ({totalResponseCount})</h3>

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
            <CommentThread
              key={comment.id}
              comment={comment}
              articleId={articleId}
              depth={0}
              onDeleted={handleTopLevelDeleted}
              onUpdated={handleTopLevelUpdated}
            />
          ))
        )}
      </div>
    </div>
  );
}
