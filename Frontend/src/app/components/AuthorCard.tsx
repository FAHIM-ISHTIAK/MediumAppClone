import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { AuthorProfile } from '../lib/api';

interface AuthorCardProps {
  author: AuthorProfile;
}

export default function AuthorCard({ author }: AuthorCardProps) {
  const { api, user } = useApp();
  const [isFollowing, setIsFollowing] = useState(author.isFollowing);
  const [followerCount, setFollowerCount] = useState(author.followers);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setIsFollowing(author.isFollowing);
    setFollowerCount(author.followers);
  }, [author.id, author.isFollowing, author.followers]);

  const handleFollow = async () => {
    if (!user || loading) return;
    const nextFollowing = !isFollowing;
    const followerDelta = nextFollowing ? 1 : -1;

    setLoading(true);
    setIsFollowing(nextFollowing);
    setFollowerCount((prev) => Math.max(0, prev + followerDelta));

    try {
      const res = nextFollowing
        ? await api.followAuthor(author.id, user.id)
        : await api.unfollowAuthor(author.id, user.id);
      setIsFollowing(res.following);
      setFollowerCount(res.followerCount);
    } catch (err) {
      setIsFollowing(!nextFollowing);
      setFollowerCount((prev) => Math.max(0, prev - followerDelta));
      console.error('Follow error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-start gap-3 py-4">
      {author.avatar && (
        <img src={author.avatar} alt={author.name} className="size-10 rounded-full" />
      )}

      <div className="flex-1 min-w-0">
        <h3 className="font-medium">{author.name}</h3>
        <p className="text-sm text-gray-600 line-clamp-2">{author.bio}</p>
        <p className="text-xs text-gray-500 mt-1">
          {followerCount.toLocaleString()} followers · {author.articles} articles
        </p>
      </div>

      {user && (
        <button
          onClick={handleFollow}
          disabled={loading}
          className={`px-4 py-1.5 text-sm rounded-full border transition-colors ${
            isFollowing
              ? 'border-gray-300 text-gray-700 hover:border-gray-400'
              : 'border-black bg-black text-white hover:bg-gray-800'
          }`}
        >
          {isFollowing ? 'Following' : 'Follow'}
        </button>
      )}
    </div>
  );
}
