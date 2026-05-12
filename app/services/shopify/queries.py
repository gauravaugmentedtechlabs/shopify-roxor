ORDER_QUERY = """
query Order($id: ID!, $cursor: String) {
  order(id: $id) {
    id
    name
    currencyCode
    customer { id displayName email }
    shippingAddress { name address1 city zip countryCodeV2 }
    lineItems(first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      edges {
        node {
          id
          sku
          quantity
          variant { id sku inventoryItem { id } }
          discountedUnitPriceSet { shopMoney { amount currencyCode } }
        }
      }
    }
  }
}
"""

ORDER_SEARCH_QUERY = """
query Orders($query: String!) {
  orders(first: 1, query: $query) {
    edges {
      node {
        id
        name
        fulfillmentOrders(first: 25) {
          edges {
            node {
              id
              status
              lineItems(first: 100) {
                edges { node { id sku remainingQuantity totalQuantity } }
              }
            }
          }
        }
      }
    }
  }
}
"""

VARIANT_BY_SKU_QUERY = """
query ProductVariants($query: String!) {
  productVariants(first: 1, query: $query) {
    edges { node { id sku inventoryItem { id } } }
  }
}
"""
