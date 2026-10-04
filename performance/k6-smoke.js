import http from 'k6/http';
import { check, sleep } from 'k6';

const base = __ENV.BASE_URL || 'http://localhost:8000';
export const options = {
  vus: 10,
  duration: '30s',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

export default function () {
  const health = http.get(`${base}/health`);
  check(health, { 'health is ready': (r) => r.status === 200 });
  const schema = http.get(`${base}/openapi.json`);
  check(schema, { 'OpenAPI schema is served': (r) => r.status === 200 });
  sleep(1);
}
