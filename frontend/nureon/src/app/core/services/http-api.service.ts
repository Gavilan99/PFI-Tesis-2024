import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { Question } from '../models/question.model';
import { TestAttempt } from '../models/test-attempt.model';
import { NewResponseInput, TestResponse } from '../models/response.model';
import { Result } from '../models/result.model';

// Real backend implementation. Not built yet — Flask/Cognito integration is
// a later stage (see the redesign plan's "Dependencias externas"). Exists
// now purely so the API_SERVICE provider in app.module.ts has a real class
// to switch to when environment.useMockApi is false, without any component
// needing to change once these methods are actually implemented against
// environment.apiBaseUrl.
@Injectable()
export class HttpApiService implements ApiService {
  constructor(private readonly http: HttpClient) {}

  createTestAttempt(): Observable<TestAttempt> {
    return this.notImplemented('createTestAttempt');
  }

  getQuestions(_attemptId: string): Observable<Question[]> {
    return this.notImplemented('getQuestions');
  }

  submitResponse(_attemptId: string, _response: NewResponseInput): Observable<TestResponse> {
    return this.notImplemented('submitResponse');
  }

  completeTestAttempt(_attemptId: string): Observable<TestAttempt> {
    return this.notImplemented('completeTestAttempt');
  }

  getResult(_attemptId: string): Observable<Result> {
    return this.notImplemented('getResult');
  }

  getLatestAttempt(): Observable<TestAttempt | null> {
    return this.notImplemented('getLatestAttempt');
  }

  private notImplemented<T>(method: string): Observable<T> {
    throw new Error(
      `HttpApiService.${method}() is not implemented yet — backend integration is a later ` +
        'stage. Set environment.useMockApi = true to use MockApiService instead.',
    );
  }
}
