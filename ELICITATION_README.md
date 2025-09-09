# FastMCP Elicitation Implementation

This project demonstrates the implementation of FastMCP elicitation in a movie recommendation system. The elicitation feature allows MCP servers to request structured input from users during tool execution, making interactions more dynamic and personalized.

## What is Elicitation?

Elicitation allows MCP servers to request structured input from users during tool execution. Instead of requiring all inputs upfront, servers can interactively ask users for information as needed - like prompting for missing parameters, requesting clarification, or gathering additional context.

**Key Benefits:**
- **Dynamic Interactions**: Ask for more information as needed
- **Better User Experience**: Guide users through complex workflows
- **Structured Input**: Use dataclasses for type-safe responses
- **Flexible Workflows**: Handle optional parameters gracefully

## Implementation Overview

### Enhanced `suggest_movie` Tool

The `suggest_movie` tool has been enhanced to demonstrate both traditional and elicitation-based approaches:

#### Traditional Mode (No Elicitation)
```python
# Immediate results based on genre
result = await client.suggest_movie(genre="Action", use_elicitation=False)
```

**Behavior:**
- Takes a genre parameter
- Returns immediate movie recommendations
- No user interaction required
- Fast and straightforward

#### Elicitation Mode (With Elicitation)
```python
# Interactive preference gathering
result = await client.suggest_movie(use_elicitation=True)
```

**Behavior:**
- No initial parameters required
- Asks user for detailed preferences
- Gathers feedback on recommendations
- Provides personalized results

## Files Structure

```
app/
├── models/
│   └── elicitation.py          # Elicitation response models
├── mcp/
│   ├── mcp_routes.py          # Original routes (complex)
│   └── mcp_routes_clean.py    # Clean version with elicitation
└── data/
    └── movies.json            # Movie database

test_elicitation.py            # Test script for elicitation
ELICITATION_README.md          # This file
```

## Elicitation Models

The system uses structured dataclasses for elicitation responses:

### UserPreferences
```python
@dataclass
class UserPreferences:
    preferred_genres: List[str]
    max_duration_minutes: Optional[int] = None
    min_rating: Optional[str] = None
    include_foreign_films: bool = True
    preferred_decade: Optional[str] = None
    mood: Optional[str] = None
```

### RecommendationFeedback
```python
@dataclass
class RecommendationFeedback:
    liked_movies: List[str]
    disliked_movies: List[str]
    additional_preferences: Optional[str] = None
    rating_accuracy: Optional[int] = None
```

## How to Test

### 1. Install Dependencies
```bash
pip install -e .
```

### 2. Run the Test Script
```bash
python test_elicitation.py
```

### 3. Expected Output

The test script will demonstrate:

1. **Traditional Mode**: Immediate results for "Action" genre
2. **Elicitation Mode**: Interactive preference gathering and personalized results

## Comparison: With vs Without Elicitation

### Traditional Mode
```
Input: genre="Action"
Output: Immediate list of Action movies
User Experience: Quick, but generic
```

### Elicitation Mode
```
Input: use_elicitation=True
Process: 
  1. Ask for user preferences
  2. Gather detailed criteria
  3. Provide personalized recommendations
  4. Collect feedback for improvement
Output: Tailored recommendations based on user input
User Experience: Interactive, personalized, but takes longer
```

## Key Differences

| Aspect | Traditional Mode | Elicitation Mode |
|--------|------------------|------------------|
| **Speed** | Fast | Slower (interactive) |
| **Personalization** | None | High |
| **User Input** | Single parameter | Multiple structured inputs |
| **Results** | Generic | Tailored to preferences |
| **Learning** | None | Improves over time with feedback |

## Use Cases

### Traditional Mode is Better For:
- Quick searches
- Simple queries
- When user knows exactly what they want
- Batch processing

### Elicitation Mode is Better For:
- Personalized recommendations
- Complex preferences
- Discovery scenarios
- User onboarding
- Improving recommendation quality

## Technical Implementation

### Server-Side (MCP Server)
```python
@mcp.tool()
async def suggest_movie(genre: str = None, context: Context = None, use_elicitation: bool = False) -> str:
    if use_elicitation:
        # Elicitation mode
        preferences = await context.elicit(
            "What are your movie preferences?",
            UserPreferences,
            description="Please tell us about your movie preferences."
        )
        # Process preferences and get personalized results
    else:
        # Traditional mode
        # Direct genre-based search
```

### Client-Side (Elicitation Handler)
```python
async def elicitation_handler(message: str, response_type: type, params, context):
    if response_type == UserPreferences:
        # Handle user preferences elicitation
        return UserPreferences(preferred_genres=["Action", "Comedy"])
    elif response_type == RecommendationFeedback:
        # Handle feedback elicitation
        return RecommendationFeedback(liked_movies=["Movie1", "Movie2"])
```

## Future Enhancements

1. **More Elicitation Tools**: Add elicitation to other tools
2. **Advanced Filtering**: Implement more sophisticated preference matching
3. **User Profiles**: Store and reuse elicited preferences
4. **Machine Learning**: Use feedback to improve recommendation algorithms
5. **Progressive Disclosure**: Ask for more details only when needed

## Resources

- [FastMCP Elicitation Documentation](https://gofastmcp.com/clients/elicitation#basic-example)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP GitHub Repository](https://github.com/jlowin/fastmcp)

## Conclusion

This implementation demonstrates how elicitation can transform a simple movie recommendation tool into an interactive, personalized experience. The key is finding the right balance between automation and user interaction based on your specific use case.

The enhanced `suggest_movie` tool serves as a perfect example of how to implement elicitation while maintaining backward compatibility with traditional usage patterns.
