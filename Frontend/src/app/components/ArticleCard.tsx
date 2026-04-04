import { Link } from 'react-router';
import { ArticleSummary } from '../lib/api';

interface ArticleCardProps {
  article: ArticleSummary;
}

export default function ArticleCard({ article }: ArticleCardProps) {
  return (
    <Link to={`/article/${article.id}`} className="block group">
      <article className="py-6 border-b border-gray-200">
        <div className="flex gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              {article.author.avatar && (
                <img
                  src={article.author.avatar}
                  alt={article.author.name}
                  className="size-6 rounded-full"
                />
              )}
              <span className="text-sm">{article.author.name}</span>
              {article.publication && (
                <>
                  <span className="text-sm text-gray-400">in</span>
                  <span className="text-sm font-medium">{article.publication}</span>
                </>
              )}
            </div>

            <h2 className="text-xl font-bold mb-2 group-hover:underline line-clamp-2">
              {article.title}
            </h2>

            <p className="text-gray-600 mb-4 line-clamp-2">{article.subtitle}</p>

            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>{article.date}</span>
              <span>{article.readingTime} min read</span>
              <span>👏 {article.claps}</span>
              <div className="flex gap-2">
                {article.tags.slice(0, 2).map((tag) => (
                  <span key={tag} className="bg-gray-100 px-2 py-1 rounded-full text-xs">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {article.coverImage && (
            <img
              src={article.coverImage}
              alt={article.title}
              className="w-28 h-28 object-cover rounded"
            />
          )}
        </div>
      </article>
    </Link>
  );
}
