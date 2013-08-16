from diff_match_patch import diff_match_patch as diff_match_patch


class SublimeDMP(DMP):

	  def patch_apply(self, patches, view):
    """Merge a set of patches onto the sublime view.  Return a patched text, as well
    as a list of true/false values indicating which patches were applied.

    Args:
      patches: Array of Patch objects.
      text: Old text.

    Returns:
      Two element Array, containing the new text and an array of boolean values.
    """

    if not patches:
      return (text, [], [])

    # Deep copy the patches so that no changes are made to originals.
    patches = self.patch_deepCopy(patches)

    nullPadding = self.patch_addPadding(patches)
    text = nullPadding + text + nullPadding
    self.patch_splitMax(patches)

    # delta keeps track of the offset between the expected and actual location
    # of the previous patch.  If there are patches expected at positions 10 and
    # 20, but the first patch was found at 12, delta is 2 and the second patch
    # has an effective expected position of 22.
    delta = 0
    results = []
    changes = []
    for patch in patches:
      expected_loc = patch.start2 + delta
      text1 = self.diff_text1(patch.diffs)
      end_loc = -1
      if len(text1) > self.Match_MaxBits:
        # patch_splitMax will only provide an oversized pattern in the case of
        # a monster delete.
        start_loc = self.match_main(text, text1[:self.Match_MaxBits],
                                    expected_loc)
        if start_loc != -1:
          end_loc = self.match_main(text, text1[-self.Match_MaxBits:],
              expected_loc + len(text1) - self.Match_MaxBits)
          if end_loc == -1 or start_loc >= end_loc:
            # Can't find valid trailing context.  Drop this patch.
            start_loc = -1
      else:
        start_loc = self.match_main(text, text1, expected_loc)
      if start_loc == -1:
        # No match found.  :(
        results.append(False)
        # Subtract the delta for this failed patch from subsequent patches.
        delta -= patch.length2 - patch.length1
      else:
        # Found a match.  :)
        results.append(True)
        delta = start_loc - expected_loc
        if end_loc == -1:
          text2 = text[start_loc : start_loc + len(text1)]
        else:
          text2 = text[start_loc : end_loc + self.Match_MaxBits]
        if text1 == text2:
          # Perfect match, just shove the replacement text in.
          text = (text[:start_loc] + self.diff_text2(patch.diffs) +
                      text[start_loc + len(text1):])
        else:
          # Imperfect match.
          # Run a diff to get a framework of equivalent indices.
          diffs = self.diff_main(text1, text2, False)
          if (len(text1) > self.Match_MaxBits and
              self.diff_levenshtein(diffs) / float(len(text1)) >
              self.Patch_DeleteThreshold):
            # The end points match, but the content is unacceptably bad.
            results[-1] = False
          else:
            self.diff_cleanupSemanticLossless(diffs)
            index1 = 0
            for (op, data) in patch.diffs:
              if op != self.DIFF_EQUAL:
                index2 = self.diff_xIndex(diffs, index1)
              if op == self.DIFF_INSERT:  # Insertion
                change = ('i', start_loc+index2, data)
                changes.append(change)
                text = text[:start_loc + index2] + data + text[start_loc +
                                                               index2:]
              elif op == self.DIFF_DELETE:  # Deletion
                change = ('d', start_loc + index2, start_loc +
                    self.diff_xIndex(diffs, index1 + len(data)))
                changes.append(change)
                text = text[:start_loc + index2] + text[start_loc +
                    self.diff_xIndex(diffs, index1 + len(data)):]
              if op != self.DIFF_DELETE:
                index1 += len(data)
    # Strip the padding off.
    text = text[len(nullPadding):-len(nullPadding)]
    return (text, results, changes)
