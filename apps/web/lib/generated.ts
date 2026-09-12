export interface paths {
  "/api/v1/generate": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Generate */
    post: operations["generate_api_v1_generate_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/health/live": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Live */
    get: operations["live_api_v1_health_live_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/api/v1/health/ready": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Ready */
    get: operations["ready_api_v1_health_ready_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
}
export type webhooks = Record<string, never>;
export interface components {
  schemas: {
    /** DraftItem */
    DraftItem: {
      /** Itemid */
      itemId: string;
      /** Sourcefragmentids */
      sourceFragmentIds: string[];
      /** Text */
      text: string;
    };
    /** @enum {string} */
    EngineVersion: "structured-llm-v1" | "rules-fallback-v1";
    /** @enum {string} */
    ErrorCode:
      | "MALFORMED_JSON"
      | "REQUEST_IN_PROGRESS"
      | "PAYLOAD_TOO_LARGE"
      | "UNSUPPORTED_MEDIA_TYPE"
      | "VALIDATION_ERROR"
      | "RATE_LIMITED"
      | "SERVICE_UNAVAILABLE"
      | "INTERNAL_ERROR";
    /** ErrorDetail */
    ErrorDetail: {
      /** Clientrequestid */
      clientRequestId: string | null;
      code: components["schemas"]["ErrorCode"];
      /** Fielderrors */
      fieldErrors: {
        [key: string]: string[];
      };
      /** Message */
      message: string;
      /**
       * Requestid
       * Format: uuid
       */
      requestId: string;
    };
    /** ErrorResponse */
    ErrorResponse: {
      error: components["schemas"]["ErrorDetail"];
    };
    /** GenerateRequest */
    GenerateRequest: {
      /**
       * Clientrequestid
       * Format: uuid
       */
      clientRequestId: string;
      /** Rawnotes */
      rawNotes: string;
      styleProfile: components["schemas"]["StyleProfile"];
    };
    /** GenerateResponse */
    GenerateResponse: {
      /**
       * Clientrequestid
       * Format: uuid
       */
      clientRequestId: string;
      draft: components["schemas"]["StandupDraft"];
      /** Durationms */
      durationMs: number;
      engineVersion: components["schemas"]["EngineVersion"];
      /**
       * Requestid
       * Format: uuid
       */
      requestId: string;
      /** Warnings */
      warnings: components["schemas"]["GenerationWarning"][];
    };
    /** GenerationWarning */
    GenerationWarning: {
      code: components["schemas"]["WarningCode"];
      /** Itemid */
      itemId: string | null;
      /** Message */
      message: string;
      section: components["schemas"]["Section"] | null;
      /** Sourcefragmentids */
      sourceFragmentIds: string[];
      /** Warningid */
      warningId: string;
    };
    /** Liveness */
    Liveness: {
      /**
       * Status
       * @default ok
       * @constant
       */
      status: "ok";
    };
    /** @enum {string} */
    PrimaryState:
      "configured" | "unconfigured" | "available" | "degraded" | "circuit_open";
    /** @enum {string} */
    ProfileId:
      "concise-bullets" | "standard-update" | "async-detail" | "custom";
    /** Readiness */
    Readiness: {
      primaryFormatter: components["schemas"]["PrimaryState"];
      /**
       * Status
       * @default ready
       * @constant
       */
      status: "ready";
    };
    /** @enum {string} */
    Section: "yesterday" | "today" | "blockers";
    /** SectionHeaders */
    SectionHeaders: {
      /** Blockers */
      blockers: string;
      /** Today */
      today: string;
      /** Yesterday */
      yesterday: string;
    };
    /** StandupDraft */
    StandupDraft: {
      /** Blockers */
      blockers: components["schemas"]["DraftItem"][];
      /** Today */
      today: components["schemas"]["DraftItem"][];
      /** Yesterday */
      yesterday: components["schemas"]["DraftItem"][];
    };
    /** StyleProfile */
    StyleProfile: {
      headers: components["schemas"]["SectionHeaders"];
      id: components["schemas"]["ProfileId"];
      /** Label */
      label: string;
      /**
       * Layout
       * @enum {string}
       */
      layout: "bullets" | "paragraphs";
      /** Preferredmaxitemspersection */
      preferredMaxItemsPerSection: number;
      /**
       * Tone
       * @enum {string}
       */
      tone: "direct" | "neutral-professional";
      /**
       * Verbosity
       * @enum {string}
       */
      verbosity: "brief" | "standard";
    };
    /** @enum {string} */
    WarningCode:
      | "FALLBACK_USED"
      | "UNCERTAIN_SECTION"
      | "POSSIBLE_FACT_OMISSION"
      | "PROFILE_LIMIT_EXCEEDED"
      | "LANGUAGE_NOT_EVALUATED";
  };
  responses: never;
  parameters: never;
  requestBodies: never;
  headers: never;
  pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
  generate_api_v1_generate_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["GenerateRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["GenerateResponse"];
        };
      };
      /** @description Bad Request */
      400: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Conflict */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Content Too Large */
      413: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unsupported Media Type */
      415: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Unprocessable Content */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Too Many Requests */
      429: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Internal Server Error */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
      /** @description Service Unavailable */
      503: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorResponse"];
        };
      };
    };
  };
  live_api_v1_health_live_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Liveness"];
        };
      };
    };
  };
  ready_api_v1_health_ready_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Readiness"];
        };
      };
    };
  };
}
