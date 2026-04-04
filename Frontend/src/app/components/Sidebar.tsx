import { Link, useLocation, useNavigate } from 'react-router';
import { Home, Library, User, LogOut } from 'lucide-react';
import { useApp } from '../context/AppContext';

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut, loading } = useApp();

  const isActive = (path: string) => location.pathname === path;

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
  };

  return (
    <div className="fixed left-0 top-0 h-screen w-64 border-r border-gray-200 bg-white p-6 flex flex-col">
      <Link to="/home" className="block mb-10">
        <h1 className="text-3xl font-serif">Medium</h1>
      </Link>

      <nav className="space-y-2 flex-1">
        <Link
          to="/home"
          className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
            isActive('/home') ? 'bg-gray-100 font-medium' : 'hover:bg-gray-50'
          }`}
        >
          <Home className="size-5" />
          <span>Home</span>
        </Link>

        <Link
          to="/library"
          className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
            isActive('/library') ? 'bg-gray-100 font-medium' : 'hover:bg-gray-50'
          }`}
        >
          <Library className="size-5" />
          <span>Library</span>
        </Link>

        <Link
          to="/profile"
          className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
            isActive('/profile') ? 'bg-gray-100 font-medium' : 'hover:bg-gray-50'
          }`}
        >
          <User className="size-5" />
          <span>Profile</span>
        </Link>
      </nav>

      {/* User info at bottom */}
      {loading ? (
        <div className="border-t border-gray-200 pt-4 mt-4 animate-pulse">
          <div className="flex items-center gap-3 mb-3">
            <div className="size-8 rounded-full bg-gray-200" />
            <div className="flex-1 min-w-0 space-y-2">
              <div className="h-3 w-24 rounded bg-gray-200" />
              <div className="h-3 w-32 rounded bg-gray-100" />
            </div>
          </div>
          <div className="h-8 rounded bg-gray-100" />
        </div>
      ) : user ? (
        <div className="border-t border-gray-200 pt-4 mt-4">
          <div className="flex items-center gap-3 mb-3">
            {user.avatar && (
              <img src={user.avatar} alt={user.name} className="size-8 rounded-full" />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user.name}</p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
          </div>
          <button
            onClick={handleSignOut}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-black transition-colors w-full px-2 py-1.5 hover:bg-gray-50 rounded"
          >
            <LogOut className="size-4" />
            <span>Sign out</span>
          </button>
        </div>
      ) : null}
    </div>
  );
}
