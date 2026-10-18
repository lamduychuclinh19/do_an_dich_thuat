import ContentRequestInbox from "../components/ContentRequestInbox";
import "./ApprovalPages.css";

export default function PoiApprovalPage() {
  return (
    <main className="approval-page">
      <header className="approval-page-heading">
        <p>QUẢN LÝ TÀI KHOẢN</p>
        <h1>Duyệt địa điểm</h1>
        <span>Xem và xử lý yêu cầu tạo hoặc cập nhật địa điểm từ Chủ địa điểm.</span>
      </header>
      <ContentRequestInbox type="POI" />
    </main>
  );
}
