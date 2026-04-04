import {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  useRef,
  ReactNode,
  useCallback,
} from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase";
import { ApiClient, UserInfo } from "../lib/api";
import { queryCache } from "../lib/queryCache";

interface AppContextType {
  /** The logged-in user profile (from local DB via /auth/me). null while loading or when not authed. */
  user: UserInfo | null;
  /** True while the initial auth check is running. */
  loading: boolean;
  /** The API client instance – always available, but auth-requiring calls need a logged-in user. */
  api: ApiClient;
  /** Trigger Google OAuth sign-in via Supabase. */
  signInWithGoogle: () => Promise<void>;
  /** Sign out and clear local state. */
  signOut: () => Promise<void>;
  /** Reader font size preference (UI-only state). */
  fontSize: number;
  setFontSize: (size: number) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [fontSize, setFontSize] = useState(18);
  const latestTokenRef = useRef<string | null>(null);

  // Build a stable ApiClient that always reads the freshest Supabase token.
  const api = useMemo(
    () =>
      new ApiClient(async () => latestTokenRef.current),
    [],
  );

  const loadUserProfile = useCallback(
    async (syncFirst: boolean) => {
      if (syncFirst) {
        await api.syncUser();
      }

      try {
        return await api.getMe();
      } catch (err) {
        if (
          !syncFirst &&
          err instanceof Error &&
          err.message.includes("User not synced")
        ) {
          await api.syncUser();
          return api.getMe();
        }
        throw err;
      }
    },
    [api],
  );

  const restoreUser = useCallback(
    async (session: Session | null, syncFirst = false) => {
      latestTokenRef.current = session?.access_token ?? null;

      if (!session) {
        setUser(null);
        return;
      }

      try {
        setUser(await loadUserProfile(syncFirst));
      } catch (err) {
        console.error("Failed to sync/fetch user:", err);
        setUser(null);
      }
    },
    [loadUserProfile],
  );

  // ── Auth state listener ──────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;

    // 1. Check current session on mount
    supabase.auth
      .getSession()
      .then(async ({ data: { session } }) => {
        await restoreUser(session);
        if (!cancelled) {
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error(err);
        if (!cancelled) {
          setUser(null);
          setLoading(false);
        }
      });

    // 2. Subscribe to auth changes (login, logout, token refresh)
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      latestTokenRef.current = session?.access_token ?? null;

      if (event === "INITIAL_SESSION") {
        return;
      }

      if (event === "SIGNED_OUT") {
        setUser(null);
        setLoading(false);
        // Clear all cached responses so a new user starts with a fresh slate
        queryCache.clear();
        return;
      }

      if (event === "TOKEN_REFRESHED") {
        return;
      }

      if (
        event === "SIGNED_IN" ||
        event === "USER_UPDATED"
      ) {
        setLoading(true);
        await restoreUser(session, true);
        if (!cancelled) {
          setLoading(false);
        }
      }
    });

    return () => {
      cancelled = true;
      subscription.unsubscribe();
    };
  }, [restoreUser]);

  // ── Actions ──────────────────────────────────────────────────────────────

  const signInWithGoogle = useCallback(async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/home` },
    });
    if (error) console.error("Google sign-in error:", error);
  }, []);

  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
    setUser(null);
  }, []);

  return (
    <AppContext.Provider
      value={{
        user,
        loading,
        api,
        signInWithGoogle,
        signOut,
        fontSize,
        setFontSize,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within an AppProvider");
  return ctx;
}
