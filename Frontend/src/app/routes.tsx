import { createBrowserRouter } from 'react-router';
import SignUp from './pages/SignUp';
import Home from './pages/Home';
import ArticleReader from './pages/ArticleReader';
import Library from './pages/Library';
import Profile from './pages/Profile';

export const router = createBrowserRouter([
  {
    path: '/',
    Component: SignUp,
  },
  {
    path: '/home',
    Component: Home,
  },
  {
    path: '/article/:id',
    Component: ArticleReader,
  },
  {
    path: '/library',
    Component: Library,
  },
  {
    path: '/profile',
    Component: Profile,
  },
]);
