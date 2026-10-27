import 'package:flutter/material.dart';
import 'package:ghajini_app/core/theme.dart';

class PersonCard extends StatelessWidget {
  final String name;
  final String relationship;
  final String? notes;
  final String? photoUrl;
  final VoidCallback? onTap;
  final VoidCallback? onDelete;

  const PersonCard({
    super.key,
    required this.name,
    required this.relationship,
    this.notes,
    this.photoUrl,
    this.onTap,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: "Person card: $name, your $relationship",
      child: Card(
        color: GhajiniTheme.cardWhite,
        margin: const EdgeInsets.symmetric(vertical: 8),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(GhajiniTheme.cardRadius),
          side: const BorderSide(color: GhajiniTheme.borderLight, width: 1.5),
        ),
        elevation: 2,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(GhajiniTheme.cardRadius),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Row(
              children: [
                // Avatar
                Container(
                  width: 68,
                  height: 68,
                  decoration: BoxDecoration(
                    color: GhajiniTheme.softCream,
                    shape: BoxShape.circle,
                    border: Border.all(color: GhajiniTheme.borderLight, width: 2),
                  ),
                  child: Center(
                    child: Text(
                      name.isNotEmpty ? name.substring(0, 1).toUpperCase() : "?",
                      style: const TextStyle(
                        fontFamily: 'serif',
                        fontSize: 30,
                        fontWeight: FontWeight.bold,
                        color: GhajiniTheme.primaryOrange,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 18),

                // Details
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        name,
                        style: const TextStyle(
                          fontFamily: 'serif',
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          color: GhajiniTheme.darkBrown,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        relationship.toUpperCase(),
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: GhajiniTheme.primaryOrange,
                          letterSpacing: 0.5,
                        ),
                      ),
                      if (notes != null && notes!.isNotEmpty) ...[
                        const SizedBox(height: 6),
                        Text(
                          notes!,
                          style: const TextStyle(
                            fontSize: 16,
                            color: GhajiniTheme.mutedBrown,
                            height: 1.3,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ],
                  ),
                ),

                if (onDelete != null)
                  IconButton(
                    icon: const Icon(Icons.delete_outline, color: GhajiniTheme.emergencyRed, size: 28),
                    onPressed: onDelete,
                    tooltip: "Delete person",
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
