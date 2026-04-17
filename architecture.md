# Pomodoro Timer Webアプリケーション アーキテクチャ案

## 1. 目的
本ドキュメントは、Flask + HTML/CSS/JavaScript で実装するポモドーロタイマーのアーキテクチャ方針を定義する。

主な目的は以下の通り。
- UIモックに沿った使いやすいタイマー体験を提供する
- クライアントとサーバーの責務を明確に分離する
- ユニットテストしやすい構造を最初から採用する
- 将来拡張（設定変更、通知、統計、ユーザー対応）に耐える

## 2. 全体方針
- クライアントは「表示・操作・タイマー進行」を担当する
- サーバーは「記録・集計・永続化」を担当する
- ビジネスルールはフレームワーク依存コードから分離する

責務分離の観点で、次の層構造を採用する。

1. Presentation層
- Flaskルート（HTML返却・APIエンドポイント）
- HTML/CSS/JavaScriptによるUI

2. Application層（UseCase層）
- セッション完了記録
- 日次進捗取得
- 必要に応じて設定更新

3. Domain層
- セッション種別、時間、完了条件などのルール
- 状態遷移ルール（作業/休憩）

4. Infrastructure層
- SQLiteによるデータ永続化
- Repository実装
- 時刻取得実装（Clock）

## 3. 推奨ディレクトリ構成
以下は 1.pomodoro 配下での推奨例。

- 1.pomodoro/
- 1.pomodoro/app.py
- 1.pomodoro/templates/index.html
- 1.pomodoro/static/css/style.css
- 1.pomodoro/static/js/app.js
- 1.pomodoro/static/js/state.js
- 1.pomodoro/static/js/timer.js
- 1.pomodoro/pomodoro/application/use_cases.py
- 1.pomodoro/pomodoro/domain/models.py
- 1.pomodoro/pomodoro/domain/services.py
- 1.pomodoro/pomodoro/domain/clock.py
- 1.pomodoro/pomodoro/infrastructure/repositories/sqlite_repository.py
- 1.pomodoro/pomodoro/infrastructure/db.py
- 1.pomodoro/tests/

補足。
- app.py は配線（DI、ルーティング、初期化）中心に保つ
- ドメインルールは domain に集約し、Flask から直接書かない

## 4. バックエンド設計
### 4.1 API設計（最小）
1. GET /api/progress/today
- 役割: 当日の進捗（完了回数、集中時間）を返す
- レスポンス例:
  - completed_sessions: number
  - focused_seconds: number

2. POST /api/sessions/complete
- 役割: セッション完了の記録
- リクエスト例:
  - session_type: "work" | "break"
  - started_at: ISO-8601
  - ended_at: ISO-8601
  - duration_seconds: number
  - completed: true

### 4.2 データモデル（最小）
セッション記録は以下を保持。
- id
- session_type
- started_at
- ended_at
- duration_seconds
- completed
- created_at

### 4.3 UseCase分離
UseCaseはフレームワーク非依存で実装する。
- complete_session(command)
- get_today_progress(query)

Flaskルートは以下のみ担当。
- 入力検証
- UseCase呼び出し
- レスポンス変換

## 5. フロントエンド設計
### 5.1 状態管理
UI状態を単一の state に集約する。

例。
- mode: "work" | "break"
- status: "idle" | "running" | "paused" | "completed"
- remainingSeconds
- sessionDurationSeconds
- cycleCount
- todayCompleted
- todayFocusedSeconds

状態更新は reducer 方式を推奨。
- nextState = reducer(state, event)

イベント例。
- START
- TICK
- RESET
- COMPLETE
- SWITCH_MODE

### 5.2 タイマー精度
setInterval の回数で減算せず、終了予定時刻との差分で残り時間を算出する。

計算例。
- remaining = max(0, endTime - now)

これにより、タブ非アクティブ時のズレを抑制できる。

### 5.3 表示ロジック分離
- timer.js: 残り時間、進捗率、完了判定の計算（純粋関数）
- state.js: reducer とイベント処理
- app.js: DOM描画、ユーザー操作、API連携

## 6. 状態遷移モデル
基本遷移。
1. idle -> running（開始）
2. running -> completed（0秒到達）
3. running -> idle（リセット）
4. completed -> idle（次セッション準備）
5. completed 後、モード切替（work <-> break）

不正遷移を reducer 側で拒否し、UIイベントを安全化する。

## 7. テスト容易性を高める追加設計
### 7.1 サーバー側
1. Repository 抽象化
- Domain/Application は抽象インターフェースに依存
- 本番は SQLite 実装
- テストは Fake/InMemory 実装

2. Clock 抽象化
- 現在時刻取得を Clock 経由にする
- テストでは固定時刻を注入

3. 値オブジェクトの導入
- SessionType、DurationSeconds などで不正値を早期排除

4. ルートを薄く保つ
- ルート関数に分岐ロジックを置かない

### 7.2 クライアント側
1. 純粋関数中心の設計
- 時間計算、進捗率計算、状態遷移を純粋関数化

2. APIクライアント分離
- fetch 直書きを避け、モジュール化
- テストで通信を差し替え可能にする

3. render(state) 分離
- 描画とロジックを分離し、テスト観点を明確化

## 8. テスト戦略
### 8.1 テストピラミッド
- ユニットテスト（多）: domain/application
- 結合テスト（中）: Flask API + DB
- E2E（少）: 主要フローのみ

### 8.2 優先テストケース
1. ドメイン
- セッション完了判定
- モード切替
- 不正入力の拒否

2. アプリケーション
- 完了記録時に正しく保存される
- 日次集計が正しく算出される

3. API
- 正常系レスポンス
- バリデーションエラー
- 想定外エラー時のハンドリング

4. 時間境界
- 日付跨ぎ（00:00）
- タイムゾーン考慮

## 9. 拡張方針
- 設定（作業/休憩時間）を永続化可能な設計にする
- 通知（音、ブラウザ通知）をイベント起点で追加可能にする
- 将来ユーザー機能を追加できるよう user_id 拡張余地を確保する

## 10. 実装ステップ（推奨）
1. Flaskで画面表示と静的ファイル配信を整備
2. UIモックに沿ったHTML/CSS実装
3. フロントの状態管理・タイマー計算を実装
4. セッション完了APIを実装
5. SQLite保存と日次集計APIを実装
6. テスト（domain/application/API）を追加
7. 通知や設定画面などの拡張を段階的に追加
