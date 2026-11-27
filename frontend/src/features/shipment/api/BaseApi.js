import { ApiError } from './ApiError';

/** Base class: adds the service prefix and turns axios errors into ApiError. */
export class BaseApi {
  constructor(http, prefix) {
    this.http = http;
    this.prefix = prefix;
  }

  async request(method, path, { data, params } = {}) {
    try {
      const response = await this.http.request({
        method, url: this.prefix + path, data, params, paramsSerializer: { indexes: null },
      });
      return response.data;
    } catch (error) {
      throw ApiError.from(error);
    }
  }
}
