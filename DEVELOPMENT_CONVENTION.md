api_conventions:
  restful_resource_naming:
    rules:
      - "use_plural_nouns_for_resources"
      - "use_kebab_case_for_multiword_resources"
      - "keep_urls_lowercase"
    
    examples:
      single_resource:
        - "GET /api/users"
        - "GET /api/users/:id"
        - "POST /api/users"
        - "PUT /api/users/:id"
        - "PATCH /api/users/:id"
        - "DELETE /api/users/:id"
      
      multiword_resources:
        - "GET /api/user-profiles"
        - "GET /api/payment-methods"

  http_methods:
    GET:
      purpose: "retrieve_data"
      properties: ["safe", "idempotent"]
    
    POST:
      purpose: "create_new_resources"
    
    PUT:
      purpose: "replace_entire_resource"
    
    PATCH:
      purpose: "partial_update"
    
    DELETE:
      purpose: "remove_resource"

  nested_resources:
    description: "for_clear_parent_child_relationships"
    examples:
      - "GET /api/users/:userId/orders"
      - "POST /api/users/:userId/orders"
      - "GET /api/shops/:shopId/products"

  query_parameters:
    use_cases: ["filtering", "sorting", "pagination"]
    examples:
      - "GET /api/products?category=electronics&sort=price-asc"
      - "GET /api/users?page=2&limit=20&status=active"

  implementation_template:
    javascript_router:
      - "router.get('/api/products', getProducts)"
      - "router.get('/api/products/:id', getProduct)"
      - "router.post('/api/products', createProduct)"
      - "router.patch('/api/products/:id', updateProduct)"
      - "router.delete('/api/products/:id', deleteProduct)"