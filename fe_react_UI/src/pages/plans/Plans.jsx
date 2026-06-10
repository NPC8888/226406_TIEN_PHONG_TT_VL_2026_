import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { listPlans, purchasePlan, submitPostForm } from "@/services/apiService";

const formatPlanPrice = (plan) => {
  if (plan.currency === "VND") {
    return new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: "VND",
      maximumFractionDigits: 0,
    }).format(plan.price_cents || 0);
  }

  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: plan.currency || "USD",
  }).format((plan.price_cents || 0) / 100);
};

const readPaymentNotice = () => {
  const params = new URLSearchParams(window.location.search);
  const paymentStatus = params.get("payment");
  const invoice = params.get("invoice");

  if (paymentStatus === "success") {
    return {
      type: "success",
      text: `Thanh toán đã được gửi tới SePay${invoice ? ` cho đơn ${invoice}` : ""}. Credit sẽ được cộng khi IPN xác nhận thành công.`,
    };
  }
  if (paymentStatus === "cancel") {
    return { type: "error", text: "Bạn đã hủy thanh toán SePay. Đơn nạp credit vẫn ở trạng thái chờ." };
  }
  if (paymentStatus === "error") {
    return { type: "error", text: "Thanh toán SePay chưa thành công. Vui lòng thử lại hoặc chọn gói khác." };
  }
  return null;
};

function Plans() {
  const navigate = useNavigate();
  const { user, activeSubscription, refreshSubscription, refreshProfile } = useAuth();
  const [plans, setPlans] = useState([]);
  const [initialNotice] = useState(readPaymentNotice);
  const [message, setMessage] = useState(initialNotice?.type === "success" ? initialNotice.text : null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(initialNotice?.type === "error" ? initialNotice.text : null);
  const [pendingPayment, setPendingPayment] = useState(null);

  useEffect(() => {
    const loadPlans = async () => {
      try {
        const data = await listPlans();
        setPlans(data);
      } catch (err) {
        setError(err.message || "Không thể tải gói credit.");
      }
    };
    loadPlans();
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const paymentStatus = params.get("payment");
    if (!paymentStatus) return;

    if (paymentStatus === "success") {
      refreshSubscription();
      refreshProfile();
    }
    window.history.replaceState({}, document.title, window.location.pathname);
  }, [refreshProfile, refreshSubscription]);

  const handlePurchase = async (planSlug) => {
    if (!user) {
      navigate("/login", { state: { from: { pathname: "/plans" } } });
      return;
    }

    setMessage(null);
    setError(null);
    setLoading(true);

    try {
      const response = await purchasePlan(planSlug);
      if (response.method === "QR") {
        setPendingPayment({
          ...response,
          starting_balance: Number(activeSubscription?.credit_balance || 0),
        });
        setMessage(`Đã tạo đơn ${response.invoice_number}. Quét QR hoặc chuyển khoản đúng nội dung để được cộng credit tự động.`);
        setLoading(false);
        return;
      }
      setMessage(`Đang chuyển sang SePay để thanh toán đơn ${response.invoice_number}.`);
      submitPostForm(response.checkout_url, response.fields);
    } catch (err) {
      setError(err.message || "Không thể tạo đơn thanh toán SePay. Vui lòng thử lại.");
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!pendingPayment) return undefined;

    const refreshPaymentState = async () => {
      await refreshSubscription();
      await refreshProfile();
    };
    const intervalId = window.setInterval(refreshPaymentState, 5000);
    return () => window.clearInterval(intervalId);
  }, [pendingPayment, refreshProfile, refreshSubscription]);

  useEffect(() => {
    if (!pendingPayment || !activeSubscription) return;

    const expectedBalance = Number(pendingPayment.starting_balance || 0) + Number(pendingPayment.credits || 0);
    const currentBalance = Number(activeSubscription.credit_balance || 0);
    if (currentBalance >= expectedBalance) {
      const timeoutId = window.setTimeout(() => {
        setMessage(`Đã xác nhận thanh toán đơn ${pendingPayment.invoice_number}. Credit đã được cộng vào tài khoản.`);
        setPendingPayment(null);
      }, 0);
      return () => window.clearTimeout(timeoutId);
    }
    return undefined;
  }, [activeSubscription, pendingPayment]);

  return (
    <main className="plans-page">
      <section className="plans-card">
        <div className="plans-header">
          <div className="auth-kicker">Credit</div>
          <h2>Nạp credit để tạo nội dung</h2>
          <p>Thanh toán qua SePay. Credit chỉ được cộng sau khi hệ thống nhận IPN thanh toán thành công.</p>

          <div className="subscription-banner">
            {activeSubscription ? (
              <>
                Số dư hiện tại: <strong>{Number(activeSubscription.credit_balance || 0).toFixed(6)} credit</strong>. Đã dùng{" "}
                {(activeSubscription.total_input_tokens || 0).toLocaleString("vi-VN")} input token và{" "}
                {(activeSubscription.total_output_tokens || 0).toLocaleString("vi-VN")} output token.
              </>
            ) : (
              "Tài khoản mới được cấp 1 credit miễn phí."
            )}
          </div>
        </div>

        <div className="plans-grid">
          {plans.map((plan) => (
            <article key={plan.slug} className="plan-card">
              <div>
                <h3>{plan.name}</h3>
                <p className="plan-description">{plan.description || `Nạp ${plan.credit_amount || plan.id} credit vào tài khoản.`}</p>
              </div>
              <div className="plan-meta">
                <span>{plan.credit_amount || plan.id} credit</span>
                <strong>{formatPlanPrice(plan)}</strong>
              </div>
              <button type="button" className="btn btn-generate" onClick={() => handlePurchase(plan.slug)} disabled={loading}>
                Thanh toán SePay
              </button>
            </article>
          ))}
        </div>

        {loading && <div className="auth-message">Đang tạo đơn thanh toán...</div>}
        {message && <div className="auth-success">{message}</div>}
        {error && <div className="auth-error">{error}</div>}

        {pendingPayment && (
          <section className="payment-panel">
            <div>
              <h3>Thanh toán chuyển khoản</h3>
              <p>Chuyển đúng số tiền và nội dung để SePay WebHook tự động xác nhận.</p>
            </div>
            {pendingPayment.qr_url && <img src={pendingPayment.qr_url} alt={`QR thanh toán ${pendingPayment.invoice_number}`} />}
            <dl>
              <div>
                <dt>Ngân hàng</dt>
                <dd>{pendingPayment.bank_code}</dd>
              </div>
              <div>
                <dt>Số tài khoản</dt>
                <dd>{pendingPayment.account_number}</dd>
              </div>
              <div>
                <dt>Chủ tài khoản</dt>
                <dd>{pendingPayment.account_holder || "-"}</dd>
              </div>
              <div>
                <dt>Số tiền</dt>
                <dd>{formatPlanPrice({ price_cents: pendingPayment.amount_vnd, currency: "VND" })}</dd>
              </div>
              <div>
                <dt>Nội dung</dt>
                <dd>{pendingPayment.transfer_content}</dd>
              </div>
            </dl>
          </section>
        )}
      </section>
    </main>
  );
}

export default Plans;
