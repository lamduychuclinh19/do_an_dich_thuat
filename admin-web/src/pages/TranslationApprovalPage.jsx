import ContentRequestInbox from "../components/ContentRequestInbox";
import "./ApprovalPages.css";

export default function TranslationApprovalPage() {
  return (
    <main className="approval-page">
      <header className="approval-page-heading">
        <p>QUẢN LÝ TÀI KHOẢN</p>
        <h1>Duyệt bản dịch</h1>
        <span>Xem và xử lý yêu cầu tạo hoặc cập nhật thuyết minh/audio từ Chủ địa điểm.</span>
      </header>
      <ContentRequestInbox type="TRANSLATION" />
    </main>
  );
}
