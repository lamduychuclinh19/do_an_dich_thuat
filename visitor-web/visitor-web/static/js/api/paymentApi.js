import { http } from "./http.js";

export const createOrder = () => http("POST", "/api/pay/create");
export const getOrderStatus = (orderId) => http("GET", "/api/pay/status", { params: { order_id: orderId } });
