import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, Link, useLocation, useNavigate } from 'react-router';
import { useApp } from '../context/AppContext';
import {
  Bookmark,
  BookmarkCheck,
  Share2,
  MessageCircle,
  ChevronLeft,
  Type,
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import CommentSection from '../components/CommentSection';
import ClapButton from '../components/ClapButton';
import InlineCommentPopup from '../components/InlineCommentPopup';
import { ArticleDetail, InlineResponseItem } from '../lib/api';

export default function ArticleReader() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { api, user, fontSize, setFontSize } = useApp();

  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isSaved, setIsSaved] = useState(false);
  const [inlineComments, setInlineComments] = useState<InlineResponseItem[]>([]);

  const [showFontAdjuster, setShowFontAdjuster] = useState(false);
  const [showHighlightMenu, setShowHighlightMenu] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  const [highlightPosition, setHighlightPosition] = useState({ x: 0, y: 0 });
  const [showInlineComment, setShowInlineComment] = useState(false);
<<<<<<< HEAD
=======
  const [selectedParagraphIndex, setSelectedParagraphIndex] = useState(0);
>>>>>>> main
  const [showShareMenu, setShowShareMenu] = useState(false);
  const [savingHighlight, setSavingHighlight] = useState(false);
  const [savingArticle, setSavingArticle] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  // Track time spent reading
  const readStartRef = useRef<number>(Date.now());
  const maxReadPercentageRef = useRef<number>(0);
  const resumePercentage = Math.max(
    0,
    Math.min(100, Number(new URLSearchParams(location.search).get('resume') || 0))
  );

  // Track scroll progress (read percentage)
  useEffect(() => {
    const handleScroll = () => {
      if (!contentRef.current) return;
      const rect = contentRef.current.getBoundingClientRect();
      const contentTop = rect.top + window.scrollY;
      const contentHeight = rect.height;
      if (contentHeight <= 0) return;

      const scrollBottom = window.scrollY + window.innerHeight;
      const scrolled = scrollBottom - contentTop;
      const percentage = Math.min(100, Math.max(0, Math.round((scrolled / contentHeight) * 100)));
      if (percentage > maxReadPercentageRef.current) {
        maxReadPercentageRef.current = percentage;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    // Run once on mount to capture initial position
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, [article]);

  useEffect(() => {
    if (!article || !contentRef.current || resumePercentage <= 0) return;

    const contentRect = contentRef.current.getBoundingClientRect();
    const contentTop = contentRect.top + window.scrollY;
    const targetScrollY = Math.max(
      contentTop + (resumePercentage / 100) * contentRect.height - window.innerHeight,
      0
    );

    window.requestAnimationFrame(() => {
      window.scrollTo({ top: targetScrollY, behavior: 'smooth' });
      maxReadPercentageRef.current = Math.max(maxReadPercentageRef.current, resumePercentage);
      navigate(location.pathname, { replace: true });
    });
  }, [article, location.pathname, navigate, resumePercentage]);

  // Fetch article
  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api
      .getArticle(id)
      .then((data) => {
        setArticle(data);
        readStartRef.current = Date.now();
      })
      .catch((err) => console.error('Failed to load article:', err))
      .finally(() => setLoading(false));
  }, [api, id]);

  // Fetch inline responses
  useEffect(() => {
    if (!id) return;
    api
      .getInlineResponses(id)
      .then((res) => setInlineComments(res.data))
      .catch(() => {});
  }, [api, id]);

  // Check if article is saved (we get this from saved articles list)
  useEffect(() => {
    if (!user || !id) return;
    api
      .getSavedArticleState(user.id, id)
      .then((res) => {
        setIsSaved(res.saved);
      })
      .catch(() => {});
  }, [api, user, id]);

  // Restore saved highlights from the backend onto the DOM
  useEffect(() => {
    if (!user || !id || !article || !contentRef.current) return;

    const colorCssMap: Record<string, string> = {
      yellow: '#FEF3C7',
      blue: '#DBEAFE',
      green: '#DCFCE7',
    };

    const paintHighlightOnDom = (container: HTMLElement, text: string, cssColor: string) => {
      // Walk all text nodes in the container and find a match
      const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
      let node: Text | null;
      while ((node = walker.nextNode() as Text | null)) {
        const idx = node.textContent?.indexOf(text) ?? -1;
        if (idx === -1) continue;
        // Don't re-highlight text already inside a highlight span
        if (node.parentElement?.getAttribute('data-highlight')) continue;

        const range = document.createRange();
        range.setStart(node, idx);
        range.setEnd(node, idx + text.length);
        const span = document.createElement('span');
        span.style.backgroundColor = cssColor;
        span.style.padding = '2px 0';
        span.setAttribute('data-highlight', 'true');
        range.surroundContents(span);
        return true;
      }
      return false;
    };

    api
      .getArticleHighlights(id, user.id)
      .then((res) => {
        if (!contentRef.current) return;
        const paragraphs = contentRef.current.children;
        for (const hl of res.data) {
          const cssColor = colorCssMap[hl.color] || '#FEF3C7';
          // Try the specific paragraph first if we have a paragraphIndex
          if (hl.paragraphIndex != null && paragraphs[hl.paragraphIndex]) {
            if (paintHighlightOnDom(paragraphs[hl.paragraphIndex] as HTMLElement, hl.text, cssColor)) continue;
          }
          // Fallback: search the entire content area
          paintHighlightOnDom(contentRef.current!, hl.text, cssColor);
        }
      })
      .catch((err) => console.error('Failed to restore highlights:', err));
  }, [api, user, id, article]);

  // Track reading time and progress reliably — fires on navigation, tab close, tab switch
  useEffect(() => {
    const sendTracking = () => {
      if (!id || !user) return;
      const minutes = Math.round((Date.now() - readStartRef.current) / 60000);
      const readPct = maxReadPercentageRef.current;
      if (minutes > 0 || readPct > 0) {
        api.trackReadingBeacon(id, Math.max(minutes, 0), readPct);
      }
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        sendTracking();
      }
    };

    const handleBeforeUnload = () => {
      sendTracking();
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', handleBeforeUnload);
      // Also fire on SPA navigation (React cleanup)
      sendTracking();
    };
  }, [api, id, user]);

  // Text selection handler for highlights
  useEffect(() => {
    const handleSelection = () => {
      const selection = window.getSelection();
      const text = selection?.toString().trim();

      if (text && text.length > 0 && contentRef.current?.contains(selection?.anchorNode || null)) {
        setSelectedText(text);
        const range = selection?.getRangeAt(0);
        const rect = range?.getBoundingClientRect();

        if (rect) {
          setHighlightPosition({
            x: rect.left + rect.width / 2,
            y: rect.top - 10,
          });
          setShowHighlightMenu(true);
        }
      } else {
        setShowHighlightMenu(false);
      }
    };

    document.addEventListener('mouseup', handleSelection);
    return () => document.removeEventListener('mouseup', handleSelection);
  }, []);

  const handleHighlight = useCallback(
    async (color: string) => {
      if (!selectedText || !article || !user || savingHighlight) return;

      // Map CSS colors to backend enum values
      const colorMap: Record<string, string> = {
        '#FEF3C7': 'yellow',
        '#DBEAFE': 'blue',
        '#DCFCE7': 'green',
      };
      const apiColor = colorMap[color] || 'yellow';
      const selection = window.getSelection();
      const paintedSpans: HTMLSpanElement[] = [];

      // Compute paragraph index for reliable re-application later
      let paragraphIndex: number | undefined;
      if (selection && contentRef.current) {
        let node = selection.anchorNode as Node | null;
        while (node && node.parentNode !== contentRef.current) {
          node = node.parentNode;
        }
        if (node && contentRef.current) {
          const children = Array.from(contentRef.current.children);
          const idx = children.indexOf(node as Element);
          if (idx >= 0) paragraphIndex = idx;
        }
      }

      try {
        setSavingHighlight(true);

        // Paint the highlight immediately so the UI feels responsive.
        // Use a safe approach that works even when the selection spans
        // across existing highlight <span> elements.
        if (selection && selection.rangeCount > 0) {
          const range = selection.getRangeAt(0);
          try {
            // Fast path: works when selection doesn't cross element boundaries
            const span = document.createElement('span');
            span.style.backgroundColor = color;
            span.style.padding = '2px 0';
            span.setAttribute('data-highlight', 'true');
            range.surroundContents(span);
            paintedSpans.push(span);
          } catch {
            // Slow path: selection crosses existing highlight spans.
            // Extract contents, wrap each text node individually.
            const fragment = range.extractContents();
            const walker = document.createTreeWalker(fragment, NodeFilter.SHOW_TEXT);
            const textNodes: Text[] = [];
            while (walker.nextNode()) {
              textNodes.push(walker.currentNode as Text);
            }
            for (const textNode of textNodes) {
              const span = document.createElement('span');
              span.style.backgroundColor = color;
              span.style.padding = '2px 0';
              span.setAttribute('data-highlight', 'true');
              textNode.parentNode!.insertBefore(span, textNode);
              span.appendChild(textNode);
              paintedSpans.push(span);
            }
            range.insertNode(fragment);
          }
        }

        setShowHighlightMenu(false);
        window.getSelection()?.removeAllRanges();

        await api.createHighlight(article.id, user.id, {
          text: selectedText,
          color: apiColor,
          paragraphIndex,
        });
      } catch (err) {
        console.error('Failed to save highlight:', err);

        for (const span of paintedSpans) {
          if (span.parentNode) {
            const parent = span.parentNode;
            while (span.firstChild) {
              parent.insertBefore(span.firstChild, span);
            }
            parent.removeChild(span);
          }
        }
      } finally {
        setSavingHighlight(false);
      }
    },
    [selectedText, article, user, api, savingHighlight]
  );

  const handleInlineComment = () => {
<<<<<<< HEAD
=======
    // Compute paragraph index from current selection
    const selection = window.getSelection();
    let pIdx = 0;
    if (selection && contentRef.current) {
      let node = selection.anchorNode as Node | null;
      while (node && node.parentNode !== contentRef.current) {
        node = node.parentNode;
      }
      if (node && contentRef.current) {
        const children = Array.from(contentRef.current.children);
        const idx = children.indexOf(node as Element);
        if (idx >= 0) pIdx = idx;
      }
    }
    setSelectedParagraphIndex(pIdx);
>>>>>>> main
    setShowInlineComment(true);
    setShowHighlightMenu(false);
  };

  const handleToggleSave = async () => {
    if (!user || !id || savingArticle) return;
    const nextSaved = !isSaved;

    try {
      setSavingArticle(true);
      setIsSaved(nextSaved);

      if (nextSaved) {
        await api.saveArticle(user.id, id);
      } else {
        await api.unsaveArticle(user.id, id);
      }
    } catch (err) {
      setIsSaved(!nextSaved);
      console.error('Save toggle failed:', err);
    } finally {
      setSavingArticle(false);
    }
  };

  const handleShare = (platform: string) => {
    const url = window.location.href;
    const text = article?.title || '';

    const shareUrls: Record<string, string> = {
      twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
      linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`,
    };

    if (shareUrls[platform]) {
      window.open(shareUrls[platform], '_blank', 'width=600,height=400');
    }
    setShowShareMenu(false);
  };

  const handleInlineCommentCreated = (newComment: InlineResponseItem) => {
    setInlineComments((prev) => [...prev, newComment]);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white">
        <Sidebar />
        <div className="ml-64 max-w-3xl mx-auto px-12 py-12">
          <div className="animate-pulse space-y-6">
            <div className="h-10 bg-gray-200 rounded w-3/4" />
            <div className="h-6 bg-gray-200 rounded w-1/2" />
            <div className="h-48 bg-gray-100 rounded" />
            <div className="space-y-3">
              <div className="h-4 bg-gray-100 rounded" />
              <div className="h-4 bg-gray-100 rounded" />
              <div className="h-4 bg-gray-100 rounded w-2/3" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="min-h-screen bg-white">
        <Sidebar />
        <div className="ml-64 flex items-center justify-center h-screen">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4">Article not found</h2>
            <Link to="/home" className="text-blue-600 hover:underline">
              Go back to home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <Sidebar />

      <div className="ml-64">
        {/* Header Actions */}
        <div className="sticky top-0 bg-white border-b border-gray-200 z-10">
          <div className="max-w-3xl mx-auto px-12 py-4 flex items-center justify-between">
            <Link to="/home" className="flex items-center gap-2 text-gray-600 hover:text-black">
              <ChevronLeft className="size-5" />
              <span>Back</span>
            </Link>

            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowFontAdjuster(!showFontAdjuster)}
                className="p-2 hover:bg-gray-100 rounded-full relative"
                title="Adjust font size"
              >
                <Type className="size-5" />
              </button>

              {user && (
                <button
                  onClick={handleToggleSave}
                  disabled={savingArticle}
                  className="p-2 hover:bg-gray-100 rounded-full"
                  title={isSaved ? 'Unsave' : 'Save'}
                >
                  {isSaved ? (
                    <BookmarkCheck className="size-5 fill-current" />
                  ) : (
                    <Bookmark className="size-5" />
                  )}
                </button>
              )}

              <div className="relative">
                <button
                  onClick={() => setShowShareMenu(!showShareMenu)}
                  className="p-2 hover:bg-gray-100 rounded-full"
                  title="Share"
                >
                  <Share2 className="size-5" />
                </button>

                {showShareMenu && (
                  <div className="absolute right-0 top-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-2 w-48">
                    <button
                      onClick={() => handleShare('twitter')}
                      className="w-full text-left px-4 py-2 hover:bg-gray-100 rounded"
                    >
                      Share on Twitter
                    </button>
                    <button
                      onClick={() => handleShare('facebook')}
                      className="w-full text-left px-4 py-2 hover:bg-gray-100 rounded"
                    >
                      Share on Facebook
                    </button>
                    <button
                      onClick={() => handleShare('linkedin')}
                      className="w-full text-left px-4 py-2 hover:bg-gray-100 rounded"
                    >
                      Share on LinkedIn
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Font Adjuster */}
          {showFontAdjuster && (
            <div className="max-w-3xl mx-auto px-12 py-4 border-t border-gray-200">
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">Font size:</span>
                <input
                  type="range"
                  min="14"
                  max="24"
                  value={fontSize}
                  onChange={(e) => setFontSize(Number(e.target.value))}
                  className="flex-1"
                />
                <span className="text-sm font-medium w-12">{fontSize}px</span>
              </div>
            </div>
          )}
        </div>

        {/* Article Content */}
        <article className="max-w-3xl mx-auto px-12 py-12">
          <h1 className="text-4xl font-bold mb-4">{article.title}</h1>
          <h2 className="text-xl text-gray-600 mb-8">{article.subtitle}</h2>

          <div className="flex items-center justify-between mb-8 pb-8 border-b border-gray-200">
            <div className="flex items-center gap-3">
              {article.author.avatar && (
                <img
                  src={article.author.avatar}
                  alt={article.author.name}
                  className="size-12 rounded-full"
                />
              )}
              <div>
                <p className="font-medium">{article.author.name}</p>
                <p className="text-sm text-gray-600">
                  {article.readingTime} min read · {article.date}
                </p>
              </div>
            </div>

            {user && (
              <FollowButton authorId={article.author.id} />
            )}
          </div>

          {article.coverImage && (
            <img
              src={article.coverImage}
              alt={article.title}
              className="w-full h-96 object-cover rounded-lg mb-12"
            />
          )}

          <div
            ref={contentRef}
            className="prose prose-lg max-w-none"
            style={{ fontSize: `${fontSize}px`, lineHeight: '1.75' }}
          >
            {article.content.map((paragraph, index) => {
              if (paragraph.startsWith('## ')) {
                return (
                  <h2 key={index} className="text-2xl font-bold mt-12 mb-4">
                    {paragraph.replace('## ', '')}
                  </h2>
                );
              } else if (paragraph.startsWith('### ')) {
                return (
                  <h3 key={index} className="text-xl font-bold mt-8 mb-3">
                    {paragraph.replace('### ', '')}
                  </h3>
                );
              } else {
                return (
                  <p key={index} className="mb-6">
                    {paragraph}
                  </p>
                );
              }
            })}
          </div>

          {/* Highlight Menu */}
          {showHighlightMenu && user && (
            <div
              className="fixed bg-black text-white rounded-lg shadow-lg p-2 flex items-center gap-2 z-50"
              style={{
                left: `${highlightPosition.x}px`,
                top: `${highlightPosition.y}px`,
                transform: 'translate(-50%, -100%)',
              }}
            >
              <button
                onClick={() => handleHighlight('#FEF3C7')}
                disabled={savingHighlight}
                className="p-2 hover:bg-gray-800 rounded"
                title="Yellow highlight"
              >
                <div className="size-5 bg-yellow-200 rounded" />
              </button>
              <button
                onClick={() => handleHighlight('#DBEAFE')}
                disabled={savingHighlight}
                className="p-2 hover:bg-gray-800 rounded"
                title="Blue highlight"
              >
                <div className="size-5 bg-blue-200 rounded" />
              </button>
              <button
                onClick={() => handleHighlight('#DCFCE7')}
                disabled={savingHighlight}
                className="p-2 hover:bg-gray-800 rounded"
                title="Green highlight"
              >
                <div className="size-5 bg-green-200 rounded" />
              </button>
              <div className="w-px h-6 bg-gray-600" />
              <button
                onClick={handleInlineComment}
                className="p-2 hover:bg-gray-800 rounded flex items-center gap-1"
                title="Add comment"
              >
                <MessageCircle className="size-4" />
                <span className="text-xs">Comment</span>
              </button>
            </div>
          )}

          {/* Inline Comment Popup */}
          {showInlineComment && user && (
            <InlineCommentPopup
              articleId={article.id}
              selectedText={selectedText}
<<<<<<< HEAD
=======
              paragraphIndex={selectedParagraphIndex}
>>>>>>> main
              onClose={() => setShowInlineComment(false)}
              onCreated={handleInlineCommentCreated}
              position={highlightPosition}
            />
          )}

          {/* Display Inline Comments */}
          {inlineComments.length > 0 && (
            <div className="mt-12 pt-8 border-t border-gray-200">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <MessageCircle className="size-5" />
                Inline Comments ({inlineComments.length})
              </h3>
              <div className="space-y-4">
                {inlineComments.map((comment) => (
                  <div
                    key={comment.id}
                    className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
                  >
                    <p className="text-sm bg-gray-50 border-l-2 border-blue-400 pl-3 py-2 mb-2 italic text-gray-600">
                      "{comment.selectedText}"
                    </p>
                    <p className="text-sm text-gray-800">{comment.text}</p>
                    <p className="text-xs text-gray-500 mt-2">{comment.date}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          <div className="flex gap-2 mt-12 pt-8 border-t border-gray-200">
            {article.tags.map((tag) => (
              <span key={tag} className="bg-gray-100 px-4 py-2 rounded-full text-sm">
                {tag}
              </span>
            ))}
          </div>

          {/* Claps and Comments Count */}
          <div className="flex items-center gap-6 mt-8 py-6 border-y border-gray-200">
            <ClapButton articleId={article.id} initialClaps={article.claps} />
          </div>

          {/* Comments Section */}
          <CommentSection articleId={article.id} />
        </article>
      </div>
    </div>
  );
}

/** Small inline follow button component */
function FollowButton({ authorId }: { authorId: string }) {
  const { api, user } = useApp();
  const [following, setFollowing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (!user || !authorId) {
      setFollowing(false);
      setInitialized(true);
      return;
    }

    setInitialized(false);

    api
      .getAuthor(authorId)
      .then((author) => setFollowing(author.isFollowing))
      .catch((err) => console.error('Failed to load follow state:', err))
      .finally(() => setInitialized(true));
  }, [api, user?.id, authorId]);

  const handleClick = async () => {
    if (!user || loading || !initialized) return;
    const nextFollowing = !following;

    setLoading(true);
    setFollowing(nextFollowing);

    try {
      const res = nextFollowing
        ? await api.followAuthor(authorId, user.id)
        : await api.unfollowAuthor(authorId, user.id);
      setFollowing(res.following);
    } catch (err) {
      setFollowing(!nextFollowing);
      console.error('Follow error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading || !initialized}
      className={`px-4 py-2 rounded-full border transition-colors ${
        initialized && following
          ? 'border-gray-300 text-gray-700 hover:border-gray-400'
          : initialized
            ? 'border-black bg-black text-white hover:bg-gray-800'
            : 'border-gray-200 bg-gray-100 text-gray-400'
      }`}
    >
      {!initialized ? 'Loading...' : following ? 'Following' : 'Follow'}
    </button>
  );
}
