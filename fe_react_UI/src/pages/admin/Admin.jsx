import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import {
  getAdminDashboard,
  getAdminEnvSettings,
  getAdminPostDetail,
  loginAdmin,
  setAuthToken,
  testGeminiKey,
  updateAdminEnvSettings,
  updateModelPricing,
} from "@/services/apiService";
import logo from "@/assets/logoweb.png";
import styles from "./Admin.module.css";

const formatNumber = (value) => Number(value || 0).toLocaleString("vi-VN");
const formatVnd = (value) =>
  new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND", maximumFractionDigits: 0 }).format(Number(value || 0));
const formatCredit = (value) => Number(value || 0).toFixed(6);
const formatDate = (value) => (value ? new Date(value).toLocaleString("vi-VN") : "-");
const today = () => new Date().toISOString().slice(0, 10);

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "dashboard" },
  { id: "revenue", label: "Doanh thu", icon: "payments" },
  { id: "users", label: "Người dùng", icon: "group" },
  { id: "config", label: "Cấu hình", icon: "tune" },
  { id: "apiKeys", label: "API Keys", icon: "key" },
];

function StatPill({ label, value }) {
  return (
    <span className={styles.statPill}>
      <em>{label}</em>
      <strong>{value}</strong>
    </span>
  );
}

function MetricCard({ label, value, helper, tone = "default", icon, onClick }) {
  return (
    <button type="button" className={`${styles.metricCard} ${styles[`metric${tone}`] || ""}`} onClick={onClick}>
      <span className={styles.metricTop}>
        <span>{label}</span>
        <i className={styles.metricIcon} aria-hidden="true">{icon}</i>
      </span>
      <strong>{value}</strong>
      {helper && <em>{helper}</em>}
    </button>
  );
}

function AdminSidebar({ activeTab, onTabChange }) {
  return (
    <aside className={styles.adminSidebar}>
      <div className={styles.sidebarBrand}>
        <img src={logo} alt="" />
        <div>
          <strong>Smomer</strong>
          <span>Xưởng nội dung AI</span>
        </div>
      </div>
      <nav className={styles.sidebarNav} aria-label="Admin">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={activeTab === item.id ? styles.sidebarNavActive : ""}
            onClick={() => onTabChange(item.id)}
          >
            <i aria-hidden="true">{item.icon}</i>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}

function DateFilters({ value, onChange }) {
  return (
    <div className={styles.dateFilters}>
      <label>
        Ngày cụ thể
        <input type="date" value={value.date} onChange={(event) => onChange({ date: event.target.value, from_date: "", to_date: "" })} />
      </label>
      <label>
        Từ ngày
        <input type="date" value={value.from_date} onChange={(event) => onChange({ ...value, date: "", from_date: event.target.value })} />
      </label>
      <label>
        Đến ngày
        <input type="date" value={value.to_date} onChange={(event) => onChange({ ...value, date: "", to_date: event.target.value })} />
      </label>
      <button type="button" onClick={() => onChange({ date: "", from_date: "", to_date: "" })}>Tất cả</button>
    </div>
  );
}

function PricingRow({ pricing, onSaved }) {
  const [draft, setDraft] = useState({
    input_price_per_1m: pricing.input_price_per_1m,
    output_price_per_1m: pricing.output_price_per_1m,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await updateModelPricing(pricing.model_key, {
        display_name: pricing.display_name || "Giá model đang dùng",
        active: true,
        input_price_per_1m: Number(draft.input_price_per_1m),
        output_price_per_1m: Number(draft.output_price_per_1m),
      });
      await onSaved();
    } catch (err) {
      setError(err.message || "Không thể lưu giá model.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={styles.pricingRow}>
      <div className={styles.modelIdentity}>
        <strong>Giá tính credit</strong>
        <span>Cập nhật lần cuối: {formatDate(pricing.updated_at)}</span>
      </div>
      <label>
        USD / 1M input
        <input type="number" step="0.000001" min="0" value={draft.input_price_per_1m} onChange={(event) => setDraft({ ...draft, input_price_per_1m: event.target.value })} />
      </label>
      <label>
        USD / 1M output
        <input type="number" step="0.000001" min="0" value={draft.output_price_per_1m} onChange={(event) => setDraft({ ...draft, output_price_per_1m: event.target.value })} />
      </label>
      <button type="button" onClick={save} disabled={saving}>{saving ? "Đang lưu..." : "Lưu cấu hình giá"}</button>
      {error && <div className={styles.inlineError}>{error}</div>}
    </div>
  );
}

function EmptyState({ text }) {
  return <div className={styles.emptyState}>{text}</div>;
}

function PaymentsTable({ payments }) {
  if (!payments.length) return <EmptyState text="Chưa có hóa đơn SePay trong khoảng thời gian này." />;
  return (
    <div className={styles.dataTable}>
      <div className={styles.tableHead}>
        <span>Hóa đơn</span>
        <span>Người dùng</span>
        <span>Số tiền</span>
        <span>Trạng thái</span>
        <span>Thời gian</span>
      </div>
      {payments.map((payment) => (
        <div key={payment.id} className={styles.tableRow}>
          <strong>{payment.provider_payment_id || `#${payment.id}`}</strong>
          <span>{payment.user_email || `User #${payment.user_id}`}</span>
          <span>{payment.currency === "VND" ? formatVnd(payment.amount) : `${formatNumber(payment.amount / 100)} USD`}</span>
          <em className={payment.status === "completed" ? styles.statusCompleted : styles.statusPending}>{payment.status}</em>
          <span>{formatDate(payment.created_at)}</span>
        </div>
      ))}
    </div>
  );
}

function UsersTable({ users, posts, onPostOpen }) {
  if (!users.length) return <EmptyState text="Chưa có người dùng trong khoảng thời gian này." />;
  const postsByUser = posts.reduce((acc, post) => {
    acc[post.user_id] = [...(acc[post.user_id] || []), post];
    return acc;
  }, {});

  return (
    <div className={styles.userList}>
      {users.map((user) => (
        <article key={user.id} className={styles.userCard}>
          <div className={styles.userTopline}>
            <div>
              <strong>{user.name || "Chưa có tên"}</strong>
              <span>{user.email}</span>
            </div>
            <em className={user.role === "admin" ? styles.statusPending : styles.statusCompleted}>{user.role}</em>
          </div>
          <div className={styles.userStats}>
            <span><strong>{formatCredit(user.credit_balance)}</strong> credit</span>
            <span><strong>{formatVnd(user.total_paid_vnd)}</strong> đã nạp</span>
            <span><strong>{formatNumber(user.total_posts)}</strong> bài viết</span>
          </div>
          <div className={styles.postMiniList}>
            {(postsByUser[user.id] || []).slice(0, 6).map((post) => (
              <button key={post.id} type="button" onClick={() => onPostOpen(post.id)}>
                <span>{post.title || `Bài #${post.id}`}</span>
                <em>{formatNumber((post.input_tokens || 0) + (post.output_tokens || 0))} token</em>
              </button>
            ))}
            {!(postsByUser[user.id] || []).length && <small>Chưa có bài viết trong khoảng thời gian này.</small>}
          </div>
        </article>
      ))}
    </div>
  );
}

function PostDetailModal({ post, loading, onClose }) {
  if (!post && !loading) return null;
  return (
    <div className={styles.modalOverlay} role="dialog" aria-modal="true" aria-label="Chi tiết bài viết">
      <section className={styles.postModal}>
        <div className={styles.panelHeader}>
          <div>
            <h2>{loading ? "Đang tải..." : post.title}</h2>
            {post && <p>{post.user_email} · {formatDate(post.created_at)}</p>}
          </div>
          <button type="button" className={styles.panelAction} onClick={onClose}>Đóng</button>
        </div>
        {post && (
          <>
            <div className={styles.postStatGrid}>
              <StatPill label="LLM calls" value={formatNumber(post.llm_call_count)} />
              <StatPill label="Input" value={formatNumber(post.input_tokens)} />
              <StatPill label="Output" value={formatNumber(post.output_tokens)} />
              <StatPill label="Credit" value={formatCredit(post.credit_cost)} />
            </div>
            <div className={styles.postMeta}>
              <span>Provider: <strong>{post.ai_provider || "-"}</strong></span>
              <span>Model: <strong>{post.ai_model || "-"}</strong></span>
            </div>
            <div className={styles.postContent} dangerouslySetInnerHTML={{ __html: post.content || "" }} />
          </>
        )}
      </section>
    </div>
  );
}

function ConfigTab({ pricing, envItems, envDraft, models, loadingModels, onDraftChange, onSaveEnv, onLoadModels, onSavedPricing, saving }) {
  const modelItem = envItems.find((item) => item.key === "GEMINI_MODEL");
  const providerItem = envItems.find((item) => item.key === "AI_PROVIDER");
  return (
    <div className={styles.tabGrid}>
      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <h2>Cấu hình model hệ thống</h2>
            <p>Kiểm tra model khả dụng rồi chọn model dùng chung cho tạo bài và gợi ý.</p>
          </div>
          <button type="button" className={styles.panelAction} onClick={onLoadModels} disabled={loadingModels}>
            {loadingModels ? "Đang kiểm tra..." : "Kiểm tra model"}
          </button>
        </div>
        <div className={styles.envGrid}>
          {providerItem && (
            <label className={styles.envField}>
              <span><strong>{providerItem.label}</strong><em>{providerItem.key}</em></span>
              <select value={envDraft.AI_PROVIDER || ""} onChange={(event) => onDraftChange({ ...envDraft, AI_PROVIDER: event.target.value })}>
                {(providerItem.options || []).map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
              <small>{providerItem.description}</small>
            </label>
          )}
          {modelItem && (
            <label className={styles.envField}>
              <span><strong>{modelItem.label}</strong><em>{modelItem.key}</em></span>
              <select value={envDraft.GEMINI_MODEL || ""} onChange={(event) => onDraftChange({ ...envDraft, GEMINI_MODEL: event.target.value })}>
                <option value={envDraft.GEMINI_MODEL || ""}>{envDraft.GEMINI_MODEL || "Chọn model"}</option>
                {models.map((model) => <option key={model} value={model}>{model}</option>)}
              </select>
              <small>{modelItem.description}</small>
            </label>
          )}
        </div>
        <div className={styles.envActions}>
          <button type="button" onClick={onSaveEnv} disabled={saving}>{saving ? "Đang lưu..." : "Lưu cấu hình"}</button>
        </div>
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <h2>Giá model</h2>
            <p>Cấu hình giá token chung cho model admin đang sử dụng.</p>
          </div>
        </div>
        <div className={styles.pricingList}>
          {pricing.map((item) => <PricingRow key={item.model_key} pricing={item} onSaved={onSavedPricing} />)}
        </div>
      </section>
    </div>
  );
}

function ApiKeysTab({ envItems, envDraft, testResult, testing, onDraftChange, onSaveEnv, onTest, saving }) {
  const apiKeyItem = envItems.find((item) => item.key === "GEMINI_API_KEY");
  const serviceJsonItem = envItems.find((item) => item.key === "VERTEX_SERVICE_ACCOUNT_JSON");
  return (
    <section className={styles.panel}>
      <div className={styles.panelHeader}>
        <div>
          <h2>API Keys</h2>
          <p>Nhập Gemini API key hoặc service account JSON rồi test trước khi lưu.</p>
        </div>
      </div>
      <div className={styles.envGrid}>
        {apiKeyItem && (
          <label className={styles.envField}>
            <span><strong>{apiKeyItem.label}</strong><em>{apiKeyItem.key}</em></span>
            <div className={styles.keyInputLine}>
              <input type="password" value={envDraft.GEMINI_API_KEY || ""} onChange={(event) => onDraftChange({ ...envDraft, GEMINI_API_KEY: event.target.value })} placeholder="Nhập Gemini API key để test" />
              <button type="button" onClick={onTest} disabled={testing}>{testing ? "Đang test..." : "Test key"}</button>
            </div>
            <small>{apiKeyItem.description}</small>
          </label>
        )}
        {serviceJsonItem && (
          <label className={styles.envField}>
            <span><strong>{serviceJsonItem.label}</strong><em>{serviceJsonItem.key}</em></span>
            <textarea value={envDraft.VERTEX_SERVICE_ACCOUNT_JSON || ""} onChange={(event) => onDraftChange({ ...envDraft, VERTEX_SERVICE_ACCOUNT_JSON: event.target.value })} placeholder="Dán JSON service account vào đây" />
            <small>{serviceJsonItem.description}</small>
          </label>
        )}
      </div>
      <div className={styles.envActions}>
        <button type="button" onClick={onSaveEnv} disabled={saving}>{saving ? "Đang lưu..." : "Lưu API keys"}</button>
      </div>
      {testResult && <div className={testResult.ok ? styles.successBox : styles.errorBox}>{testResult.message}</div>}
    </section>
  );
}

function Admin() {
  const { user, loading, refreshProfile } = useAuth();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [dashboard, setDashboard] = useState(null);
  const [loadingData, setLoadingData] = useState(false);
  const [error, setError] = useState(null);
  const [loginForm, setLoginForm] = useState({ username: "admin", password: "" });
  const [loginLoading, setLoginLoading] = useState(false);
  const [filters, setFilters] = useState({ date: "", from_date: "", to_date: "" });
  const [envItems, setEnvItems] = useState([]);
  const [envDraft, setEnvDraft] = useState({});
  const [savingEnv, setSavingEnv] = useState(false);
  const [models, setModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [testingKey, setTestingKey] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [selectedPost, setSelectedPost] = useState(null);
  const [loadingPost, setLoadingPost] = useState(false);

  const metrics = dashboard?.metrics;
  const users = useMemo(() => dashboard?.users || [], [dashboard?.users]);
  const pricing = dashboard?.model_pricing || [];
  const payments = dashboard?.recent_payments || [];
  const posts = dashboard?.recent_posts || [];

  const loadDashboard = async (nextFilters = filters) => {
    setLoadingData(true);
    setError(null);
    try {
      setDashboard(await getAdminDashboard(nextFilters));
    } catch (err) {
      setError(err.message || "Không thể tải dashboard admin.");
    } finally {
      setLoadingData(false);
    }
  };

  const loadEnv = async () => {
    const response = await getAdminEnvSettings();
    const items = response.items || [];
    setEnvItems(items);
    setEnvDraft(Object.fromEntries(items.map((item) => [item.key, item.value || ""])));
  };

  useEffect(() => {
    if (user?.role === "admin") {
      loadDashboard();
      loadEnv().catch((err) => setError(err.message || "Không thể tải cấu hình."));
    }
  }, [user]);

  useEffect(() => {
    if (user?.role === "admin") {
      loadDashboard(filters);
    }
  }, [filters.date, filters.from_date, filters.to_date]);

  const submitAdminLogin = async (event) => {
    event.preventDefault();
    setLoginLoading(true);
    setError(null);
    try {
      const response = await loginAdmin(loginForm);
      setAuthToken(response.access_token);
      await refreshProfile();
    } catch (err) {
      setError(err.message || "Không thể đăng nhập admin.");
    } finally {
      setLoginLoading(false);
    }
  };

  const saveEnv = async () => {
    setSavingEnv(true);
    setError(null);
    try {
      await updateAdminEnvSettings(envItems.map((item) => ({ key: item.key, value: envDraft[item.key] ?? "" })));
      await loadEnv();
    } catch (err) {
      setError(err.message || "Không thể lưu cấu hình.");
    } finally {
      setSavingEnv(false);
    }
  };

  const loadModels = async () => {
    setLoadingModels(true);
    setTestResult(null);
    try {
      const provider = envDraft.AI_PROVIDER || "gemini_api_key";
      const apiKey = (envDraft.GEMINI_API_KEY || "").trim();
      const serviceAccountJson = (envDraft.VERTEX_SERVICE_ACCOUNT_JSON || "").trim();
      if (provider === "gemini_api_key" && (!apiKey || apiKey === "********")) {
        throw new Error("Bạn chưa nhập Gemini API key để kiểm tra model.");
      }
      if (provider === "vertex_gemini" && (!serviceAccountJson || serviceAccountJson === "********")) {
        throw new Error("Bạn chưa nhập service account JSON để kiểm tra model.");
      }
      const response = await testGeminiKey({
        provider,
        api_key: apiKey,
        service_account_json: serviceAccountJson,
        model: envDraft.GEMINI_MODEL || "",
      });
      setModels(response.models || []);
      setTestResult({ ok: response.ok, message: response.message });
    } catch (err) {
      setTestResult({ ok: false, message: err.message || "Không thể kiểm tra model." });
    } finally {
      setLoadingModels(false);
    }
  };

  const testKey = async () => {
    setTestingKey(true);
    setTestResult(null);
    try {
      const provider = envDraft.AI_PROVIDER || "gemini_api_key";
      const apiKey = (envDraft.GEMINI_API_KEY || "").trim();
      const serviceAccountJson = (envDraft.VERTEX_SERVICE_ACCOUNT_JSON || "").trim();
      if (provider === "gemini_api_key" && (!apiKey || apiKey === "********")) {
        throw new Error("Bạn chưa nhập Gemini API key để test.");
      }
      if (provider === "vertex_gemini" && (!serviceAccountJson || serviceAccountJson === "********")) {
        throw new Error("Bạn chưa nhập service account JSON để test.");
      }
      const response = await testGeminiKey({
        provider,
        api_key: apiKey,
        service_account_json: serviceAccountJson,
        model: envDraft.GEMINI_MODEL || "",
      });
      setModels(response.models || models);
      setTestResult(response);
    } catch (err) {
      setTestResult({ ok: false, message: err.message || "Không thể test key." });
    } finally {
      setTestingKey(false);
    }
  };

  const openPost = async (postId) => {
    setLoadingPost(true);
    setSelectedPost(null);
    try {
      setSelectedPost(await getAdminPostDetail(postId));
    } catch (err) {
      setError(err.message || "Không thể tải chi tiết bài viết.");
    } finally {
      setLoadingPost(false);
    }
  };

  if (loading) return <div className={styles.adminPage}>Đang kiểm tra quyền truy cập...</div>;

  if (!user) {
    return (
      <main className={styles.adminPage}>
        <section className={styles.loginCard}>
          <div>
            <span>Admin</span>
            <h1>Đăng nhập quản trị</h1>
            <p>Dùng tài khoản admin đã cấu hình trong biến môi trường backend.</p>
          </div>
          <form className={styles.adminLoginForm} onSubmit={submitAdminLogin}>
            <label>Username<input value={loginForm.username} onChange={(event) => setLoginForm({ ...loginForm, username: event.target.value })} autoComplete="username" /></label>
            <label>Password<input type="password" value={loginForm.password} onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })} autoComplete="current-password" /></label>
            <button type="submit" disabled={loginLoading}>{loginLoading ? "Đang đăng nhập..." : "Vào dashboard"}</button>
            {error && <div className={styles.errorBox}>{error}</div>}
          </form>
        </section>
      </main>
    );
  }

  if (user.role !== "admin") {
    return (
      <main className={styles.adminPage}>
        <section className={styles.deniedCard}>
          <h1>Không có quyền truy cập</h1>
          <p>Trang này chỉ dành cho tài khoản admin.</p>
        </section>
      </main>
    );
  }

  return (
    <div className={styles.adminShell}>
      <AdminSidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className={styles.adminPage}>
        <section className={styles.header}>
          <div>
            <span>Admin dashboard</span>
            <h1>Điều hành hệ thống nội dung</h1>
            <p>Theo dõi doanh thu, người dùng, bài viết và cấu hình model trong một luồng làm việc gọn.</p>
          </div>
          <div className={styles.headerActions}>
            {metrics && (
              <div className={styles.headerStats}>
                <StatPill label="Users" value={formatNumber(metrics.total_users)} />
                <StatPill label="Posts" value={formatNumber(metrics.total_posts)} />
              </div>
            )}
            <button type="button" onClick={() => loadDashboard()} disabled={loadingData}>
              <i aria-hidden="true">refresh</i>
              {loadingData ? "Đang tải..." : "Làm mới"}
            </button>
          </div>
        </section>

        {error && <div className={styles.errorBox}>{error}</div>}

        {activeTab === "dashboard" && (
          <section className={`${styles.panel} ${styles.overviewPanel}`}>
            <div className={styles.panelHeader}>
              <div>
                <h2>Tổng quan vận hành</h2>
                <p>Dashboard chỉ hiển thị các chỉ số tổng quan của hệ thống.</p>
              </div>
            </div>
            {metrics && (
              <div className={styles.metricGrid}>
                <MetricCard label="Doanh thu SePay" value={formatVnd(metrics.total_revenue_vnd)} helper="Tổng đã hoàn tất" tone="Revenue" icon="payments" />
                <MetricCard label="Đang chờ" value={formatVnd(metrics.pending_revenue_vnd)} helper={`${formatNumber(metrics.pending_payments)} đơn pending`} tone="Pending" icon="pending_actions" />
                <MetricCard label="Credit tiêu" value={formatCredit(metrics.total_credit_spent)} helper="Tổng credit đã dùng" icon="toll" />
                <MetricCard label="Người dùng mới" value={formatNumber(metrics.total_users)} helper="Theo bộ lọc thời gian" icon="group" />
                <MetricCard label="Bài đã tạo" value={formatNumber(metrics.total_posts)} helper="Theo bộ lọc thời gian" icon="article" />
                <MetricCard label="Tổng token" value={formatNumber(metrics.total_tokens)} helper={`${formatNumber(metrics.total_input_tokens)} in / ${formatNumber(metrics.total_output_tokens)} out`} icon="data_usage" />
              </div>
            )}
          </section>
        )}

        {activeTab === "revenue" && (
          <section className={styles.panel}>
            <div className={styles.panelHeader}>
              <div>
                <h2>Doanh thu</h2>
                <p>Xem doanh thu theo người dùng, hóa đơn SePay và lọc theo ngày.</p>
              </div>
            </div>
            <DateFilters value={filters} onChange={setFilters} />
            {metrics && (
              <div className={styles.metricGrid}>
                <MetricCard label="Doanh thu hoàn tất" value={formatVnd(metrics.total_revenue_vnd)} helper="Completed VND" tone="Revenue" icon="payments" />
                <MetricCard label="Đang chờ" value={formatVnd(metrics.pending_revenue_vnd)} helper={`${formatNumber(metrics.pending_payments)} hóa đơn`} tone="Pending" icon="pending_actions" />
                <MetricCard label="Người dùng nạp tiền" value={formatNumber(users.filter((item) => item.total_paid_vnd > 0 || item.total_paid_usd > 0).length)} helper="Trong danh sách hiện tại" icon="group" />
              </div>
            )}
            <PaymentsTable payments={payments} />
          </section>
        )}

        {activeTab === "users" && (
          <section className={styles.panel}>
            <div className={styles.panelHeader}>
              <div>
                <h2>Người dùng</h2>
                <p>Thống kê người dùng mới, số tiền đã nạp và các bài viết đã tạo.</p>
              </div>
            </div>
            <DateFilters value={filters} onChange={setFilters} />
            <UsersTable users={users} posts={posts} onPostOpen={openPost} />
          </section>
        )}

        {activeTab === "config" && (
          <ConfigTab
            pricing={pricing}
            envItems={envItems}
            envDraft={envDraft}
            models={models}
            loadingModels={loadingModels}
            onDraftChange={setEnvDraft}
            onSaveEnv={saveEnv}
            onLoadModels={loadModels}
            onSavedPricing={() => loadDashboard()}
            saving={savingEnv}
          />
        )}

        {activeTab === "apiKeys" && (
          <ApiKeysTab
            envItems={envItems}
            envDraft={envDraft}
            testResult={testResult}
            testing={testingKey}
            onDraftChange={setEnvDraft}
            onSaveEnv={saveEnv}
            onTest={testKey}
            saving={savingEnv}
          />
        )}
      </main>
      <PostDetailModal post={selectedPost} loading={loadingPost} onClose={() => setSelectedPost(null)} />
    </div>
  );
}

export default Admin;
