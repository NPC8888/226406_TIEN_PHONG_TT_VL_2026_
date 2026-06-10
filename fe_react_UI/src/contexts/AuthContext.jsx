import { createContext, useContext, useEffect, useState } from "react";
import {
  getAuthToken,
  setAuthToken,
  clearAuthToken,
  loginUser,
  registerUser,
  getProfile,
  getActiveSubscription,
} from "@/services/apiService";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [activeSubscription, setActiveSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  const refreshProfile = async () => {
    const token = getAuthToken();
    if (!token) {
      setUser(null);
      setActiveSubscription(null);
      return;
    }

    try {
      const profile = await getProfile();
      setUser(profile);
    } catch (error) {
      clearAuthToken();
      setUser(null);
      setActiveSubscription(null);
      return;
    }
  };

  const refreshSubscription = async () => {
    try {
      const subscription = await getActiveSubscription();
      setActiveSubscription(subscription);
    } catch {
      setActiveSubscription(null);
    }
  };

  const initializeAuth = async () => {
    const params = new URLSearchParams(window.location.search);
    const tokenFromUrl = params.get("token");
    const authErrorFromUrl = params.get("auth_error");

    if (tokenFromUrl) {
      setAuthToken(tokenFromUrl);
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (authErrorFromUrl) {
      setAuthError(authErrorFromUrl);
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    const token = getAuthToken();
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      await refreshProfile();
      await refreshSubscription();
      setAuthError(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    initializeAuth();
  }, []);

  const login = async (payload) => {
    setAuthError(null);
    const response = await loginUser(payload);
    setAuthToken(response.access_token);
    await refreshProfile();
    await refreshSubscription();
    return response;
  };

  const register = async (payload) => {
    setAuthError(null);
    const response = await registerUser(payload);
    setAuthToken(response.access_token);
    await refreshProfile();
    await refreshSubscription();
    return response;
  };

  const logout = () => {
    clearAuthToken();
    setUser(null);
    setActiveSubscription(null);
    setAuthError(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        activeSubscription,
        loading,
        authError,
        login,
        register,
        logout,
        refreshProfile,
        refreshSubscription,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside an AuthProvider");
  }
  return context;
};
