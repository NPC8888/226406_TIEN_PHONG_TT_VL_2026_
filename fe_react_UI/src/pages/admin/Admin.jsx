import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { getAdminDashboard, loginAdmin, setAuthToken, updateModelPricing } from "@/services/apiService";
import styles from "./Admin.module.css";

const formatNumber = (value) => Number(value || 0).toLocaleString("vi-VN");
const formatUsd = (value) =>
  new Intl.NumberFormat("vi-VN", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(Number(value || 0));
const formatVnd = (value) =>
  new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND", maximumFractionDigits: 0 }).format(Number(value || 0));
const formatCredit = (value) => Number(value || 0).toFixed(6);

function MetricCard({ label, value, helper }) {
  return (
    <article className={styles.metricCard}>
      <span>{label}</span>
      <strong>{value}</strong>
      {helper && <em>{helper}</em>}
    </article>
  );
}

function PricingRow({ pricing, onSaved }) {
  const [draft, setDraft] = useState({
    display_name: pricing.display_name,
    input_price_per_1m: pricing.input_price_per_1m,
    output_price_per_1m: pricing.output_price_per_1m,
    active: pricing.active,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await updateModelPricing(pricing.model_key, {
        ...draft,
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
        <strong>{pricing.model_key}</strong>
        <span>Cập nhật: {new Date(pricing.updated_at).toLocaleString("vi-VN")}</span>
      </div>
      <label>
        Tên hiển thị
        <input value={draft.display_name} onChange={(event) => setDraft({ ...draft, display_name: event.target.value })} />
      </label>
      <label>
        USD / 1M input
        <input
          type="number"
          step="0.000001"
          min="0"
          value={draft.input_price_per_1m}
          onChange={(event) => setDraft({ ...draft, input_price_per_1m: event.target.value })}
        />
      </label>
      <label>
        USD / 1M output
        <input
          type="number"
          step="0.000001"
          min="0"
          value={draft.output_price_per_1m}
          onChange={(event) => setDraft({ ...draft, output_price_per_1m: event.target.value })}
        />
      </label>
      <label className={styles.activeToggle}>
        <input type="checkbox" checked={draft.active} onChange={(event) => setDraft({ ...draft, active: event.target.checked })} />
        Đang bật
      </label>
      <button type="button" onClick={save} disabled={saving}>
        {saving ? "Đang lưu..." : "Lưu giá"}
      </button>
      {error && <div className={styles.inlineError}>{error}</div>}
    </div>
  );
}

function Admin() {
  const { user, loading, refreshProfile } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [loadingData, setLoadingData] = useState(false);
  const [error, setError] = useState(null);
  const [loginForm, setLoginForm] = useState({ username: "admin", password: "" });
  const [loginLoading, setLoginLoading] = useState(false);

  const loadDashboard = async () => {
    setLoadingData(true);
    setError(null);
    try {
      const data = await getAdminDashboard();
      setDashboard(data);
    } catch (err) {
      setError(err.message || "Không thể tải dashboard admin.");
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    if (user?.role === "admin") {
      loadDashboard();
    }
  }, [user?.role]);

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

  const metrics = dashboard?.metrics;
  const users = useMemo(() => dashboard?.users || [], [dashboard?.users]);
  const pricing = dashboard?.model_pricing || [];
  const payments = dashboard?.recent_payments || [];
  const topUsers = useMemo(
    () => [...users].sort((a, b) => Number(b.total_credit_spent || 0) - Number(a.total_credit_spent || 0)).slice(0, 8),
    [users],
  );

  if (loading) {
    return <div className={styles.adminPage}>Đang kiểm tra quyền truy cập...</div>;
  }

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
            <label>
              Username
              <input value={loginForm.username} onChange={(event) => setLoginForm({ ...loginForm, username: event.target.value })} autoComplete="username" />
            </label>
            <label>
              Password
              <input
                type="password"
                value={loginForm.password}
                onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })}
                autoComplete="current-password"
              />
            </label>
            <button type="submit" disabled={loginLoading}>
              {loginLoading ? "Đang đăng nhập..." : "Vào dashboard"}
            </button>
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
    <main className={styles.adminPage}>
      <section className={styles.header}>
        <div>
          <span>Admin dashboard</span>
          <h1>Tổng quan hệ thống</h1>
          <p>Theo dõi credit, doanh thu SePay, người dùng, token và giá model.</p>
        </div>
        <button type="button" onClick={loadDashboard} disabled={loadingData}>
          {loadingData ? "Đang tải..." : "Làm mới"}
        </button>
      </section>

      {error && <div className={styles.errorBox}>{error}</div>}

      {metrics && (
        <section className={styles.metricGrid}>
          <MetricCard label="Doanh thu SePay" value={formatVnd(metrics.total_revenue_vnd)} helper={`${formatNumber(metrics.pending_payments)} đơn đang chờ`} />
          <MetricCard label="Doanh thu USD cũ" value={formatUsd(metrics.total_revenue_usd)} />
          <MetricCard label="Credit đã tiêu" value={formatCredit(metrics.total_credit_spent)} />
          <MetricCard label="Người dùng" value={formatNumber(metrics.total_users)} />
          <MetricCard label="Bài đã tạo" value={formatNumber(metrics.total_posts)} />
          <MetricCard label="Tổng token" value={formatNumber(metrics.total_tokens)} helper={`${formatNumber(metrics.total_input_tokens)} in / ${formatNumber(metrics.total_output_tokens)} out`} />
        </section>
      )}

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <h2>Thanh toán gần đây</h2>
            <p>Đối soát các đơn SePay pending/completed và số credit tương ứng.</p>
          </div>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.userTable}>
            <thead>
              <tr>
                <th>Invoice</th>
                <th>User</th>
                <th>Credit</th>
                <th>Số tiền</th>
                <th>Trạng thái</th>
                <th>Ngày tạo</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((payment) => (
                <tr key={payment.id}>
                  <td>
                    <strong>{payment.provider_payment_id || `#${payment.id}`}</strong>
                    <span>{payment.provider}</span>
                  </td>
                  <td>{payment.user_email || `User #${payment.user_id}`}</td>
                  <td>{formatNumber(payment.credit_amount)}</td>
                  <td>{payment.currency === "VND" ? formatVnd(payment.amount) : formatUsd(payment.amount / 100)}</td>
                  <td>
                    <em className={payment.status === "completed" ? styles.roleAdmin : styles.roleUser}>{payment.status}</em>
                  </td>
                  <td>{new Date(payment.created_at).toLocaleString("vi-VN")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <h2>Giá model</h2>
            <p>Cấu hình chi phí token dùng để tính credit sau mỗi lần tạo nội dung.</p>
          </div>
        </div>
        <div className={styles.pricingList}>
          {pricing.map((item) => (
            <PricingRow key={item.model_key} pricing={item} onSaved={loadDashboard} />
          ))}
        </div>
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <h2>Người dùng nổi bật</h2>
            <p>Sắp xếp theo lượng credit đã tiêu.</p>
          </div>
        </div>
        <div className={styles.userCards}>
          {topUsers.map((item) => (
            <article key={item.id} className={styles.userCard}>
              <div>
                <strong>{item.name || item.email}</strong>
                <span>{item.email}</span>
              </div>
              <dl>
                <div>
                  <dt>Credit còn</dt>
                  <dd>{formatCredit(item.credit_balance)}</dd>
                </div>
                <div>
                  <dt>Đã tiêu</dt>
                  <dd>{formatCredit(item.total_credit_spent)}</dd>
                </div>
                <div>
                  <dt>Token</dt>
                  <dd>{formatNumber(item.total_input_tokens + item.total_output_tokens)}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.panel}>
        <div className={styles.panelHeader}>
          <div>
            <h2>Danh sách user</h2>
            <p>Hiển thị tối đa 200 tài khoản mới nhất.</p>
          </div>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.userTable}>
            <thead>
              <tr>
                <th>User</th>
                <th>Vai trò</th>
                <th>Credit còn</th>
                <th>Input token</th>
                <th>Output token</th>
                <th>Đã nạp USD</th>
                <th>Ngày tạo</th>
              </tr>
            </thead>
            <tbody>
              {users.map((item) => (
                <tr key={item.id}>
                  <td>
                    <strong>{item.name || "Chưa có tên"}</strong>
                    <span>{item.email}</span>
                  </td>
                  <td>
                    <em className={item.role === "admin" ? styles.roleAdmin : styles.roleUser}>{item.role}</em>
                  </td>
                  <td>{formatCredit(item.credit_balance)}</td>
                  <td>{formatNumber(item.total_input_tokens)}</td>
                  <td>{formatNumber(item.total_output_tokens)}</td>
                  <td>{formatUsd(item.total_paid_usd)}</td>
                  <td>{new Date(item.created_at).toLocaleDateString("vi-VN")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

export default Admin;
