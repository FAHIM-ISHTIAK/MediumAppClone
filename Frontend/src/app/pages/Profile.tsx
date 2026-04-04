import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import Sidebar from '../components/Sidebar';
import { Mail, Calendar, LogOut } from 'lucide-react';
import { ReadingAnalytics } from '../lib/api';

export default function Profile() {
  const { user, api, signOut, loading } = useApp();
  const [analytics, setAnalytics] = useState<ReadingAnalytics | null>(null);

  useEffect(() => {
    if (!user) return;
    api
      .getReadingAnalytics(user.id)
      .then(setAnalytics)
      .catch(() => {});
  }, [api, user]);

  if (loading) {
    return (
      <div className="min-h-screen bg-white">
        <Sidebar />
        <div className="ml-64 flex items-center justify-center h-screen">
          <p className="text-gray-600">Restoring your profile...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-white">
        <Sidebar />
        <div className="ml-64 flex items-center justify-center h-screen">
          <p className="text-gray-600">Please sign in to view your profile</p>
        </div>
      </div>
    );
  }

  const stats = [
    { label: 'Articles Read', value: analytics?.totalArticlesRead ?? 0 },
    { label: 'Total Time (min)', value: analytics?.totalTimeSpentMinutes ?? 0 },
    { label: 'Current Streak', value: analytics?.readingStreak.currentDays ?? 0 },
    { label: 'Top Tags', value: analytics?.topTags.length ?? 0 },
  ];

  return (
    <div className="min-h-screen bg-white">
      <Sidebar />

      <div className="ml-64 px-12 py-8">
        <div className="max-w-4xl">
          {/* Profile Header */}
          <div className="flex items-start gap-6 mb-8 pb-8 border-b border-gray-200">
            {user.avatar && (
              <img src={user.avatar} alt={user.name} className="size-24 rounded-full" />
            )}

            <div className="flex-1">
              <h1 className="text-4xl font-bold mb-2">{user.name}</h1>
              <p className="text-gray-600 mb-4">{user.bio || 'Reader and explorer'}</p>

              <div className="flex items-center gap-4 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <Mail className="size-4" />
                  <span>{user.email}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="size-4" />
                  <span>
                    Joined{' '}
                    {new Date(user.createdAt).toLocaleDateString('en-US', {
                      month: 'long',
                      year: 'numeric',
                    })}
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={signOut}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-full hover:bg-gray-50 transition-colors text-sm"
            >
              <LogOut className="size-4" />
              Sign Out
            </button>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-4 gap-6 mb-12">
            {stats.map((stat) => (
              <div key={stat.label} className="bg-gray-50 p-6 rounded-lg text-center">
                <div className="text-3xl font-bold mb-2">{stat.value}</div>
                <div className="text-sm text-gray-600">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Top Tags */}
          {analytics && analytics.topTags.length > 0 && (
            <div className="mb-8">
              <h2 className="text-2xl font-bold mb-4">Your Top Interests</h2>
              <div className="flex flex-wrap gap-3">
                {analytics.topTags.map((t) => (
                  <span key={t.tag} className="bg-gray-100 px-4 py-2 rounded-full text-sm">
                    {t.tag}{' '}
                    <span className="font-semibold text-gray-700">({t.count} articles)</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* About Section */}
          <div>
            <h2 className="text-2xl font-bold mb-4">About</h2>
            <p className="text-gray-700 leading-relaxed">
              {user.bio ||
                'A passionate reader exploring various topics shared by the Medium community.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
