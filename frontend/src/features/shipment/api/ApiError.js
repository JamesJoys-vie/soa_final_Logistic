/** Error in the team's shared shape: { code, message, details }. */
export class ApiError extends Error {
  constructor(status, body) {
    super(body?.message ?? 'Không gọi được máy chủ');
    this.status = status;
    this.code = body?.code;
    this.details = body?.details;
  }

  static from(axiosError) {
    return new ApiError(axiosError.response?.status, axiosError.response?.data);
  }

  /** The decision is recorded but Inventory has not answered: the system retries by itself. */
  get isWaitingForInventory() {
    return this.status === 502 || this.status === 504;
  }
}
